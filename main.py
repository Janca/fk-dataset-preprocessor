import json
import logging
import os.path

import fk

if __name__ == '__main__':
    if os.path.exists('env.json'):
        with open('env.json', 'r', encoding='utf-8') as f:
            env = json.load(f)

    else:
        env = {}

    preferences: fk.DatasetPreprocessorPreferences = {
        'log_level': logging.INFO,
        'suppress_invalid_keys': True,
        'input': {
            'fk:source:disk': [
                r'E:\StableDiffusion\SD Datasets\CivProfiles\001',
                r'E:\MidJourney\mj_scrape\2023102703',
                r'E:\MidJourney\mj_scrape\2023111001',
                r'E:\MidJourney\2023_05_01',
                r'E:\StableDiffusion\SD Datasets\fkNiteshade\004'
            ]
        },
        'output': {
            'fk:destination:disk': {
                'path': r'E:\StableDiffusion\SD Datasets\fkNeapolitan\001',
                'image_extension': '.jpg',
                'caption_text_extension': '.txt',
                'kwargs': {
                    'quality': 93
                }
            }
        },
        'workers': {
            'cpu_workers': 64,
            'io_workers': 8
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
                'minimum_edge': 1024
            },
            'fk:filter:image_brightness': {
                'minimum': 0.125,
                'maximum': 0.98
            },
            'fk:filter:cv2_entropy': 7.65,
            'fk:filter:cv2_blur': 400,
            'fk:filter:image_hash': {
                'hash_size': 8,
                'distance_threshold': 11
            },
            'fk:action:extract_webui_prompt': {
                'fail_on_invalid_caption': False  # if this fails, let GPT caption it
            },
            # 'fk:action:gpt_vision_captioner': {
            #     'skip_on_existing_caption': False
            # },
            'fk:action:bulk_caption_text_replacer': {
                r'fk(.+?)($|\b|\s)': ''
            },
            'fk:action:caption_text_normalizer': True,
            'fk:filter:caption_text': {
                'disallowed_tags': [
                    'anime', 'chibi', '1boy',
                    '1girl', 'manga', 'asian',
                    'korean', 'japanese', 'chinese',
                    'dragon', 'miniature', 'badly',
                    'ugly', 'deformed', 'sticker',
                    'breast', 'boob', 'tit',
                    'hot'
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
