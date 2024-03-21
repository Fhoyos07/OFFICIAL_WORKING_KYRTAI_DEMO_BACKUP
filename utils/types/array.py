from typing import Iterable


def is_array(o: any) -> bool:
    return any(isinstance(o, t) for t in (list, set, tuple))


def chunked_list(lst: list, chunk_size=100) -> Iterable[list]:
    """
    Yield successive chunk_size chunks from queryset.
    @param lst: A list of elements to be chunked.
    @param chunk_size: The size of each chunk. Defaults to 100.
    @return: An iterable of lists, where each list contains a chunk of elements from the input list.
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]
