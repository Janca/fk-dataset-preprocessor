import logging

import fk

if __name__ == '__main__':
    preferences: fk.DatasetPreprocessorPreferences = {
        'log_level': logging.DEBUG,
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
            'cpu_workers': 48
        },
        'env': {
            'openai_key': '...'
        },
        'tasks': {
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
            }
        }
    }

    preprocessor = fk.DatasetPreprocessor(preferences)

    preprocessor.register_io('fk.io')
    preprocessor.register_tasks('fk.tasks')

    preprocessor.start()
