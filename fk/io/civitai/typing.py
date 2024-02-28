import typing

NsfwLevel = typing.Literal['None', 'Soft', 'Mature', 'X']
Sort = typing.Literal['Most Buzz', 'Most Reactions', 'Most Comments', 'Newest']
Period = typing.Literal['AllTime', 'Year', 'Month', 'Week', 'Day']

Dimensions = list[int, int]


class CivitaiImageFilter(typing.TypedDict):
    require_prompt: bool | None
    disallowed_tags: list[str] | None

    stats_positive_negative_ratio: float | None

    minimum_dimensions: Dimensions | None
    maximum_dimensions: Dimensions | None


class CivitaiImageSearchQuery(typing.TypedDict):
    limit: int | None
    postId: int | None
    modelId: int | None
    modelVersionId: int | None
    username: str | None
    nsfw: list[NsfwLevel] | NsfwLevel | None
    sort: Sort | None
    period: Period | None
    page: int | None
    cursor: str | None


class CivitaiImageGenerationMetadata(typing.TypedDict):
    Size: str | None
    seed: int | None
    Model: str | None
    steps: int | None
    prompt: str | None
    negativePrompt: str | None


class CivitaiImageStats(typing.TypedDict):
    cryCount: int
    laughCount: int
    likeCount: int
    heartCount: int
    commentCount: int


class CivitaiImage(typing.TypedDict):
    id: int
    postId: int

    username: str

    url: str
    hash: str

    width: int
    height: int

    nsfw: bool
    nsfwLevel: NsfwLevel

    createdAt: str

    meta: CivitaiImageGenerationMetadata | None
    stats: CivitaiImageStats | None


class CivitaiResponseMetadata(typing.TypedDict):
    nextCursor: str | None
    nextPage: str | None


class CivitaiImageSearchResults(typing.TypedDict):
    items: list[CivitaiImage]
    metadata: CivitaiResponseMetadata | None
