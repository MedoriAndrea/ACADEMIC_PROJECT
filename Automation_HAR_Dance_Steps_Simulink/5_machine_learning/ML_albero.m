
load("features_e_pca.mat"); % Carica i dati in X (feature) e y (etichette)

%% MODELLO DA OTTIMIZZARE

% estrazione delle etichette 
etichetta = zeros(length(y),1);
for i = 1: length(y)
    if y(i) == "passo1"
        etichetta(i) = 1;
    else
        etichetta(i) = 2; 
    end
end

% Ridenominazione della matrice delle feature
feature = X_reduced; 


%% Ottimizzazione rete: Albero di decisioni
% da runnare solo 1 volta per capire quali sono i migliori iperparamentri
% per il nostro modello

rng('default');

Partition = cvpartition(etichetta,'Holdout',0.20, 'Stratify', true);
trainingInds = training(Partition);
XTrain = feature(trainingInds,:);
YTrain = etichetta(trainingInds);
testInds = test(Partition);
XTest = feature(testInds,:);
YTest = etichetta(testInds);

tTrain = array2table([XTrain YTrain]);

best_accuracy = 0;
best_params = struct();

num_learning_cycles_values = [100:100:500];
learn_rate_values = [0.1, 0.01, 0.001, 0.0001];
max_num_splits_values = [3:10];

for num_learning_cycles = num_learning_cycles_values
    for learn_rate = learn_rate_values
        for max_num_splits = max_num_splits_values

            template = templateTree('MaxNumSplits', max_num_splits, 'Reproducible', true);
            classificationEnsemble = fitcensemble(XTrain, YTrain, ...
                'Method', 'LogitBoost', ...
                'NumLearningCycles', num_learning_cycles, ...
                'Learners', template, ...
                'LearnRate', learn_rate, ...
                'ClassNames', [1; 2]);

            partitionedModel = crossval(classificationEnsemble, 'KFold', 3);
            validationAccuracy = 1 - kfoldLoss(partitionedModel);

            if validationAccuracy > best_accuracy
                best_accuracy = validationAccuracy;
                best_params.NumLearningCycles = num_learning_cycles;
                best_params.LearnRate = learn_rate;
                best_params.MaxNumSplits = max_num_splits;
            end

        end
    end
end

fprintf('Best Validation Accuracy: %.4f\n', best_accuracy);
fprintf('Best Parameters:\n');
disp(best_params);

%% Rete Ottimizzata Definitiva 

% split del dataset 
rng('default');

Partition = cvpartition(etichetta,'Holdout',0.20, 'Stratify', true);
trainingInds = training(Partition);
XTrain = feature(trainingInds,:);
YTrain = etichetta(trainingInds);
testInds = test(Partition);
XTest = feature(testInds,:);
YTest = etichetta(testInds);

tTrain = array2table([XTrain YTrain]);

% parametri ottimizzati
NumLearningCycles = 500;
MaxNumSplits = 7; 
LearnRate = 0.1;

classificationEnsemble = fitcensemble(XTrain, YTrain, ...
    'Method', 'LogitBoost', ...
    'NumLearningCycles', NumLearningCycles, ...
    'Learners', templateTree('MaxNumSplits', MaxNumSplits, 'Reproducible', true), ...
    'LearnRate', LearnRate, ...
    'ClassNames', [1; 2]);

Predizioni = predict(classificationEnsemble, XTest);

testAccuracy = 1 - loss(classificationEnsemble, XTest, YTest);
fprintf('Test Accuracy with Best Parameters: %.4f\n', testAccuracy);

modello_albero = fitctree(XTrain, YTrain, 'MinLeafSize', 5);
view(modello_albero, Mode="graph");

% salvataggio del modello per l'online 
saveLearnerForCoder(classificationEnsemble,'ML_albero_ottimizzata.mat');

% valutazione delle prestazioni 
% calcolo matrice di confusione e metriche 
confMat = confusionmat(YTest, Predizioni);
disp('Confusion Matrix:');
disp(confMat);

TP = confMat(1,1);
FN = confMat(1,2);
FP = confMat(2,1);
TN = confMat(2,2);

accuracy  = (TP + TN) / sum(confMat(:));
precision = TP / (TP + FP);
recall    = TP / (TP + FN);
f1_score  = 2 * (precision * recall) / (precision + recall);

fprintf('Test Accuracy: %.4f\n', accuracy);
fprintf('Precision: %.4f\n', precision);
fprintf('Recall: %.4f\n', recall);
fprintf('F1-score: %.4f\n', f1_score);
