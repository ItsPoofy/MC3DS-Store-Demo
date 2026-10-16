#ifndef STORE_DEMO_NATIVE_TYPES_H
#define STORE_DEMO_NATIVE_TYPES_H

typedef unsigned char u8;
typedef unsigned int u32;

typedef struct {
    char *text;
} NativeString;

/* Only the fields consumed by the original store are described here. */
typedef struct CatalogNode {
    u32 color;
    struct CatalogNode *parent;
    struct CatalogNode *left;
    struct CatalogNode *right;
    NativeString item_code;
    NativeString name;
} CatalogNode;

typedef struct {
    u8 prefix[0x10];
    CatalogNode *header;
    u32 count;
} CatalogMap;

/* nn::ec::CTR::ItemId, native metadata, and the native price string. */
typedef struct {
    u32 item_id;
    char item_code[32];
    u32 metadata[2];
    NativeString price;
} StoreItem;

typedef struct {
    StoreItem *begin;
    StoreItem *end;
    StoreItem *capacity;
} StoreItemVector;

_Static_assert(sizeof(StoreItem) == 0x30, "Native store record size");
_Static_assert(sizeof(StoreItemVector) == 12, "Native vector size");

#endif
