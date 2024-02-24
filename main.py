import json
import logging

import fk

if __name__ == '__main__':
    with open('env.json', 'r', encoding='utf-8') as f:
        env = json.load(f)

    preferences: fk.DatasetPreprocessorPreferences = {
        'log_level': logging.INFO,
        'suppress_invalid_keys': True,
        'input': {
            'fk:source:disk': r'E:\MidJourney\mj_scrape\2023102703'
        },
        'output': {
            'fk:destination:disk': {
                'path': r'E:\TEMP4',
                'image_extension': '.jpg',
                'caption_text_extension': '.txt',
                'kwargs': {
                    'quality': 85
                }
            }
        },
        'workers': {
            'cpu_workers': 128,
            'io_workers': 10
        },
        'env': env,
        'tasks': {
            # For now, you'll need to read each task to figure out the more advanced preferences for each, in the future
            # I'd like to auto generate a template for each task when passed a command line argument
            'fk:filter:image_mode': {
                'allowed_modes': 'RGB'
            },
            'fk:filter:jpg_quality': 75,
            'fk:filter:image_size': {
                'minimum_edge': 512
            },
            'fk:filter:cv2_entropy': 7.15,
            'fk:filter:cv2_blur': 300,
            'fk:filter:image_hash': {
                'hash_size': 8,
                'distance_threshold': 11
            },
            'fk:action:extract_webui_prompt': {
                'fail_on_invalid_caption': False  # if this fails, let GPT caption it
            },
            # 'fk:action:gpt_vision_captioner': True,  # defaults to skipping if caption exists
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
            'fk:action:caption_prefixer': 'fking'
        }
    }

    preprocessor = fk.DatasetPreprocessor(preferences)

    preprocessor.discover_io('fk.io')
    preprocessor.discover_tasks('fk.tasks')

    preprocessor.start()
