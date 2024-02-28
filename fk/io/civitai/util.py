import sys
import typing
import urllib.parse

from .typing import CivitaiImage, CivitaiImageStats, CivitaiImageFilter, CivitaiImageSearchQuery

_STATS_KEYS = typing.Literal['cryCount', 'laughCount', 'likeCount', 'heartCount', 'commentCount']


def stats_ratio(stats: CivitaiImageStats, positive_keys: list[_STATS_KEYS] = None) -> float:
    if positive_keys is None:
        positive_keys = ['likeCount', 'heartCount']

    positive_total = 0
    total = 0

    key: _STATS_KEYS
    keys = list(stats.keys())

    for key in keys:
        value = int(stats[key])

        if key != 'commentCount':
            total += value

        if key in positive_keys:
            positive_total += value

    return positive_total / total


def filter_image(image: CivitaiImage, filter: CivitaiImageFilter) -> bool:
    min_width, min_height = filter.get('minimum_dimensions', (0, 0))
    max_width, max_height = filter.get('maximum_dimensions', (sys.maxsize, sys.maxsize))

    require_prompt = filter.get('require_prompt', False)
    deny_list = filter.get('disallowed_tags', None)

    stats_positive_negative_ratio = filter.get('stats_positive_negative_ratio', 0)

    image_meta = image.get('meta', None)
    image_stats = image['stats']

    image_width = image['width']
    image_height = image['height']

    if require_prompt:
        if not image_meta or 'prompt' not in image_meta or not image_meta['prompt']:
            return False

    if not (min_width < image_width < max_width):
        return False

    if not (min_height < image_height < max_height):
        return False

    if deny_list:
        image_prompt = image_meta['prompt'] \
            if image_meta and 'prompt' in image_meta else None

        if image_prompt:
            image_prompt = image_prompt.lower()

            for deny_str in deny_list:
                deny_str = deny_str.lower()

                if deny_str in image_prompt:
                    return False

    if stats_positive_negative_ratio > 0:
        if not image_stats:
            return False

        if stats_ratio(image_stats) < stats_positive_negative_ratio:
            return False

    return True


def generate_search_url(query: CivitaiImageSearchQuery) -> str:
    filtered_params = {k: v for k, v in query.items() if v is not None}
    query_string = urllib.parse.urlencode(filtered_params, doseq=True)

    return f"https://civitai.com/api/v1/images?{query_string}"
