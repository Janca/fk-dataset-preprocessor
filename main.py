import json
import logging

import fk

_INSTRUCTIONS = """
Please describe this image, starting with the primary focus, and ending with the background details and styling.
Provide details like character attributes, skin color, hair color, hair style, percieved gender, emotions, and other 
facial attributes, such as freckles, eye color, facial hair, and whether the mouth is open or closed.
If the main subject is human, attempt to discern their occupation, or archetype
(wizard, paladin, nurse, lumberjack, etc).
If text appears in the image, caption with quotation marks where the text is inscribed, if possible, eg. 
"Hello" on a sign-post.
Attempt to identify mythological beings and archetypes (vampire, werewolf, leshy, mermaid, etc.), or if possible, 
directly caption a human or celebrity by name.
Finally, describe the background, first as a total, (forest, beach, indoors, living-room, etc.) and then describe 
individual elements of the background.
Take note of various lens effects, such as bokeh, depth of field, fish-eye lens, etc.
Attempt to identify the style of the image, whether it is realism, like a photograph, or some other mixed-media type 
(painting, charcoal, illustration, comic book art, anime, etc.).

The complete caption should be a a combination of both the subject, and then the background caption, blended seamlessly 
into a grammatically correct sentence or paragraph with the relevant styles. The tags field should be as if you are 
attempting to do SEO or a search on google, and be an abbreviated form of the complete caption.
Your caption text should not contain what is not available in the image, so mentions of "No other archetype...", or 
"No person...", etc should not be within the caption text. The caption should not explictly state the missing 
attributes you are looking for.
Furthermore, do not start a caption with: "This image is a...", or "The primary focus of the image...", or 
"The background..." or any other variant, it is implied that what you are captioning is an image/subject/background; 
only when it is relevant to the caption should you explicitly mention that, such as when the image is an image 
or a poster, or canvas.

Commas matter in your caption text, do not comma-separate a list of adjectives unless that adjective is not apart of 
the noun in the sentence you are writing.
An example would be, "A big, red dog..." which should instead be written as "big red dog...", or "a vibrant, 
neon-colored..." would instead be "vibrant neon-colored".

Avoid too much filler text, brief, succinct descriptions are better.

You may be given a JSON object containing the field "caption", if provided, you will reference those tags for 
additional details of the image. These tags were generated with another AI and may be partially, or completely 
inaccurate. Enhance your captions with the provided one, if you find that they correctly match the image.

Only respond with the following JSON object with your newly generated caption, not within a code block:
{"caption": "..."}
"""

if __name__ == '__main__':
    with open('env.json', 'r', encoding='utf-8') as f:
        env = json.load(f)

    print(json.dumps(env, indent=4, sort_keys=True))

    preferences: fk.DatasetPreprocessorPreferences = {
        'log_level': logging.INFO,
        'suppress_invalid_keys': True,
        'input': {
            'fk:source:disk': r'./samples'
        },
        'output': {
            'fk:destination:disk': {
                'path': r'./preprocessed',
                'image_extension': '.jpg',
                'caption_text_extension': '.txt',
                'kwargs': {
                    'quality': 1
                }
            }
        },
        'workers': {
            'cpu_workers': 12
        },
        'env': env,
        'tasks': {
            'fk:filter:jpg_quality': 75,
            'fk:filter:image_size': {
                'minimum_edge': 512
            },
            'fk:action:gpt_vision_captioner': {
                'prompt': _INSTRUCTIONS
            },
            'fk:action:caption_prefixer': 'fking',
            'fk:action:caption_text_normalizer': True,
            'fk:filter:caption_text': {
                'disallowed_tags': [
                    'anime', 'chibi', '1boy',
                    '1girl', 'manga', 'asian',
                    'korean', 'japanese', 'chinese',
                    'dragon', 'miniature', 'badly',
                    'ugly', 'deformed'
                ],
                'caption_text_required': True
            },
            # 'fk:filter:image_mode': {
            #     'allowed_modes': 'RGB'
            # },
            # 'fk:filter:jpg_quality': 75,
            # 'fk:filter:image_size': {
            #     'minimum_edge': 512
            # },
            # 'fk:filter:cv2_entropy': 7.15,
            # 'fk:filter:cv2_blur': 300,
            # 'fk:filter:image_hash': {
            #     'hash_size': 8,
            #     'distance_threshold': 11
            # }
        }
    }

    preprocessor = fk.DatasetPreprocessor(preferences)

    preprocessor.register_io('fk.io')
    preprocessor.register_tasks('fk.tasks')

    preprocessor.start()
