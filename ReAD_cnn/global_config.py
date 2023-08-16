
num_of_labels = {
    'mnist': 10,
    'fmnist': 10,
    'cifar10': 10,
    'gtsrb': 43,
    'svhn': 10,
}


cnn_config = {
    'mnist': {
        'layers_of_getting_value': [-10, -8, -6, -4],
        'neurons_of_each_layer': [320, 160, 80, 40],
        'ood_settings': ['FMNIST', 'Omniglot', 'UniformNoise_28', 'GuassianNoise_28']
    },
    'fmnist': {
        'layers_of_getting_value': [-10, -8, -6, -4],
        'neurons_of_each_layer': [320, 160, 80, 40],
        'ood_settings': ['MNIST', 'Omniglot', 'UniformNoise_28', 'GuassianNoise_28']
    },
    'cifar10': {
        'layers_of_getting_value': [-5],
        'neurons_of_each_layer': [512],
        'ood_settings': ['TinyImageNet', 'LSUN', 'iSUN', 'UniformNoise_32', 'GuassianNoise_32']
    },
    'gtsrb': {
        'layers_of_getting_value': [-5],
        'neurons_of_each_layer': [512],
        'ood_settings': ['TinyImageNet', 'LSUN', 'iSUN', 'UniformNoise_48', 'GuassianNoise_48']
    },
    'svhn': {
        'layers_of_getting_value': [-4],
        'neurons_of_each_layer': [512]
    },
}


selective_rate = 0.2
