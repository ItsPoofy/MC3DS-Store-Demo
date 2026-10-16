#include "catalog.h"
#include "native_types.h"
#include "seams.h"

typedef int (*AddRow)(void *, const void *, u32, const NativeString *);
typedef void (*Rebuild)(void *);
typedef void *(*Allocate)(u32, u32);

static StoreItem *fill_nodes(void *screen, CatalogNode *node,
                             StoreItem *next, StoreItem *limit, u32 *index) {
    if (!node) return next;
    next = fill_nodes(screen, node->left, next, limit, index);
    const char *code = node->item_code.text;
    u32 length = ((const u32 *)code)[-1];
    if (length && length < sizeof(next->item_code) && next != limit) {
        for (u32 i = 0; i < sizeof(*next); ++i) ((u8 *)next)[i] = 0;
        for (u32 i = 0; i < length; ++i) next->item_code[i] = code[i];
        next->price.text = (char *)SEAM_EmptyString;
        ((AddRow)SEAM_StoreBrowser_addRow)(screen, 0, *index, &node->name);
        ++*index;
        ++next;
    }
    return fill_nodes(screen, node->right, next, limit, index);
}

/* This entry replaces only the native store's remote catalog enumerator. */
__attribute__((section(".text.catalog_entry")))
void demo_fill_catalog(void *screen) {
    u8 *bytes = screen;
    u32 category = *(u32 *)(bytes + 0x118);
    if (category > 2) return;
    CatalogMap *map = *(CatalogMap **)(bytes + 0x13c + category * 4);
    StoreItemVector *items = (StoreItemVector *)(bytes + 0x14c + category * 12);
    if (!map || !map->header || !map->count || map->count >= 100) return;
    if (!items->begin) {
        items->begin = ((Allocate)SEAM_gstd_allocate)(map->count * sizeof(StoreItem), 0);
        items->end = items->begin;
        items->capacity = items->begin ? items->begin + map->count : 0;
    }
    if (!items->begin) return;
    /* Prices are empty shared strings: no remote currency or ownership state. */
    u32 index = 0;
    items->end = fill_nodes(screen, map->header->parent, items->begin,
                            items->capacity, &index);
}

void *demo_tick(void *screen) {
    u8 *bytes = screen;
    if (!bytes[0x113]) {
        bytes[0x113] = 1;
        ((Rebuild)SEAM_StoreBrowser_rebuild)(screen);
    }
    return screen;
}
