Removed `FilterSerializer` and `validate_jsonfilter` from the filter plugin
mechanism since they just wrap `FilterBlobSerializer`. (This also means
`FilterBlobSerializer` can no longer be in the same file as
`FilterSerializer`.)
