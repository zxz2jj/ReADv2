import pickle
import os
import pandas as pd
# import seaborn as sns
import matplotlib.pyplot as plt
from datasets import load_dataset, Dataset

from load_data import load_gtsrb, load_ood_data
from ReAD import get_neural_value, statistic_of_neural_value, \
    encode_abstraction, concatenate_data_between_layers, k_means, statistic_distance, auroc, sk_auc
from ReAD import t_sne_visualization
from global_config import num_of_labels, swin_config


if __name__ == "__main__":

    id_dataset = 'mnist'
    # id_dataset = 'fashion_mnist'
    # id_dataset = 'cifar10'
    # id_dataset = 'gtsrb'


    if id_dataset == 'mnist':
        row_names = ('image', 'label')
        finetuned_checkpoint = "./models/swin-finetuned-mnist/best"
        dataset = load_dataset("./data/mnist/")
        detector_path = './data/mnist/detector/'

    elif id_dataset == 'fashion_mnist':
        row_names = ('image', 'label')
        finetuned_checkpoint = "./models/swin-finetuned-fashion_mnist/best"
        dataset = load_dataset("./data/fashion_mnist/")
        detector_path = './data/fashion_mnist/detector/'

    elif id_dataset == 'cifar10':
        row_names = ('img', 'label')
        finetuned_checkpoint = "./models/swin-finetuned-cifar10/best"
        dataset = load_dataset("./data/cifar10/")
        detector_path = './data/cifar10/detector/'

    elif id_dataset == 'gtsrb':
        row_names = ('image', 'label')
        finetuned_checkpoint = "./models/swin-finetuned-gtsrb/best"
        dataset = load_gtsrb()
        detector_path = './data/gtsrb/detector/'

    else:
        print('dataset is not exist.')
        exit()

    rename_train_data = Dataset.from_dict({'image': dataset['train'][row_names[0]],
                                           'label': dataset['train'][row_names[1]]})
    rename_test_data = Dataset.from_dict({'image': dataset['test'][row_names[0]],
                                          'label': dataset['test'][row_names[1]]})

    train_nv_statistic = None
    k_means_centers = None
    distance_train_statistic = None
    if os.path.exists(detector_path + 'train_nv_statistic.pkl') and \
            os.path.exists(detector_path + 'k_means_centers.pkl') and \
            os.path.exists(detector_path + 'distance_of_ReAD_for_train_data.pkl'):
        print("\nDetector is existed!")
        file1 = open(detector_path + 'train_nv_statistic.pkl', 'rb')
        file2 = open(detector_path + 'k_means_centers.pkl', 'rb')
        file3 = open(detector_path + 'distance_of_ReAD_for_train_data.pkl', 'rb')
        train_nv_statistic = pickle.load(file1)
        k_means_centers = pickle.load(file2)
        distance_train_statistic = pickle.load(file3)

    else:
        if not os.path.exists(f'./data/{id_dataset}'):
            os.mkdir(f'./data/{id_dataset}')
        if not os.path.exists(detector_path):
            os.mkdir(detector_path)
        # ********************** Train Detector **************************** #
        print('\n********************** Train Detector ****************************')
        print('\nGet neural value of train dataset:')
        train_picture_neural_value = get_neural_value(id_dataset=id_dataset, dataset=rename_train_data,
                                                      checkpoint=finetuned_checkpoint, is_ood=False)
        print('\nStatistic of train data neural value:')
        train_nv_statistic = statistic_of_neural_value(id_dataset=id_dataset,
                                                       neural_value=train_picture_neural_value)
        print('finished!')

        file1 = open(detector_path + 'train_nv_statistic.pkl', 'wb')
        pickle.dump(train_nv_statistic, file1)
        file1.close()

        print('\nEncoding ReAD abstractions of train dataset:')
        train_ReAD_abstractions = encode_abstraction(id_dataset=id_dataset, neural_value=train_picture_neural_value,
                                                     train_dataset_statistic=train_nv_statistic)
        train_ReAD_concatenated = \
            concatenate_data_between_layers(id_dataset=id_dataset, data_dict=train_ReAD_abstractions)

        # visualization will need some minutes. If you want to show the visualization, please run the following codes.
        show_visualization = False
        if show_visualization:
            print('\nShow t-SNE visualization results on ReAD.')
            t_sne_visualization(data=train_ReAD_concatenated,
                                category_number=num_of_labels[id_dataset])

        print('\nK-Means Clustering of Combination Abstraction on train data:')
        k_means_centers = k_means(data=train_ReAD_concatenated,
                                  category_number=num_of_labels[id_dataset])
        file2 = open(detector_path + 'k_means_centers.pkl', 'wb')
        pickle.dump(k_means_centers, file2)
        file2.close()

        print('\nCalculate distance between abstractions and cluster centers ...')
        distance_train_statistic = statistic_distance(id_dataset=id_dataset, abstractions=train_ReAD_concatenated,
                                                      cluster_centers=k_means_centers)
        file3 = open(detector_path + 'distance_of_ReAD_for_train_data.pkl', 'wb')
        pickle.dump(distance_train_statistic, file3)
        file3.close()

    # ********************** Evaluate OOD Detection **************************** #
    print('\n********************** Evaluate OOD Detection ****************************')
    print('\nGet neural value of test dataset:')
    test_picture_neural_value = get_neural_value(id_dataset=id_dataset, dataset=rename_test_data,
                                                 checkpoint=finetuned_checkpoint, is_ood=False)
    print('\nEncoding ReAD abstraction of test dataset:')
    test_ReAD_abstractions = encode_abstraction(id_dataset=id_dataset, neural_value=test_picture_neural_value,
                                                train_dataset_statistic=train_nv_statistic)
    test_ReAD_concatenated = concatenate_data_between_layers(id_dataset=id_dataset, data_dict=test_ReAD_abstractions)
    print('\nCalculate distance between abstractions and cluster centers ...')
    test_distance = statistic_distance(id_dataset=id_dataset, abstractions=test_ReAD_concatenated,
                                       cluster_centers=k_means_centers)

    OOD_dataset = swin_config[id_dataset]['ood_settings']
    for ood in OOD_dataset:
        print('\n************Evaluating*************')
        print(f'In-Distribution Data: {id_dataset}, Out-of-Distribution Data: {ood}.')
        ood_data = load_ood_data(ood_dataset=ood)
        print('\nGet neural value of ood dataset...')
        ood_picture_neural_value = get_neural_value(id_dataset=id_dataset, dataset=ood_data,
                                                    checkpoint=finetuned_checkpoint,
                                                    is_ood=True)
        print('\nEncoding ReAD abstraction of ood dataset...')
        ood_ReAD_abstractions = encode_abstraction(id_dataset=id_dataset, neural_value=ood_picture_neural_value,
                                                   train_dataset_statistic=train_nv_statistic)
        ood_ReAD_concatenated = concatenate_data_between_layers(id_dataset=id_dataset, data_dict=ood_ReAD_abstractions)
        print('\nCalculate distance between abstractions and cluster centers ...')
        ood_distance = statistic_distance(id_dataset=id_dataset, abstractions=ood_ReAD_concatenated,
                                          cluster_centers=k_means_centers)

        # auc = auroc(distance_train_statistic, clean_distance, adv_distance, num_of_labels[clean_dataset])
        auc = sk_auc(test_distance, ood_distance, num_of_labels[id_dataset])

        print('\nPerformance of Detector:')
        print('AUROC: {:.6f}'.format(auc))
        print('*************************************\n')

        # distance_list = []
        # for i in range(10):
        #     distance_list.append(clean_distance[i]['correct_pictures'])
        #     distance_list.append(adv_distance[i]['wrong_pictures'])
        # data = {'T0': distance_list[0]}
        # data = pd.DataFrame(data, columns=['T0'])
        # data['F0'] = pd.Series(distance_list[1])
        # data['T1'] = pd.Series(distance_list[2])
        # data['F1'] = pd.Series(distance_list[3])
        # data['T2'] = pd.Series(distance_list[4])
        # data['F2'] = pd.Series(distance_list[5])
        # data['T3'] = pd.Series(distance_list[6])
        # data['F3'] = pd.Series(distance_list[7])
        # data['T4'] = pd.Series(distance_list[8])
        # data['F4'] = pd.Series(distance_list[9])
        # data['T5'] = pd.Series(distance_list[10])
        # data['F5'] = pd.Series(distance_list[11])
        # data['T6'] = pd.Series(distance_list[12])
        # data['F6'] = pd.Series(distance_list[13])
        # data['T7'] = pd.Series(distance_list[14])
        # data['F7'] = pd.Series(distance_list[15])
        # data['T8'] = pd.Series(distance_list[16])
        # data['F8'] = pd.Series(distance_list[17])
        # data['T9'] = pd.Series(distance_list[18])
        # data['F9'] = pd.Series(distance_list[19])
        # data = pd.DataFrame(data)
        # sns.boxplot(data=data)
        # plt.xticks(fontsize=15)
        # plt.yticks(fontsize=15)
        # plt.show()

