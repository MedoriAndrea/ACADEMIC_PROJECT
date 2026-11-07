clear all
close all

%% 1) Caricamento Dati
data = load("features_e_pca.mat");

X_reduced = data.X_reduced;      % Nxk
y_raw     = data.y;              % Nx1 

% estrazione labels
labels = zeros(length(y_raw),1);
for i = 1: length(y_raw)
    if y_raw(i) == "passo1"
        labels(i) = 1;
    else
        labels(i) = 2; 
    end
end

fprintf("Dati caricati: %d campioni, %d componenti PCA.\n", ...
    size(X_reduced,1), size(X_reduced,2));

%% 2) Suddivisione Iniziale (Hold-Out)
rng('default');
cv_main = cvpartition(labels, "HoldOut", 0.20, 'Stratify', true);

idx_trainval = training(cv_main);
idx_test     = test(cv_main);

X_trainval = X_reduced(idx_trainval, :);
Y_trainval = labels(idx_trainval);

X_test = X_reduced(idx_test, :);
Y_test = labels(idx_test);

%% 3) Parametri Grid Search
kernel_scales   = [0.1, 1, 10];
box_constraints = [2, 4];
k_fold = 5;

%% 4) Inizializzazione strutture
best_models = struct('svm_rbf', [], 'svm_linear',[]);
best_val_accuracies = struct('svm_rbf', 0, 'svm_linear', 0);
best_hyperparameters = struct('svm_rbf', [], 'svm_linear',[]);
classifiers = {'rbf', 'linear'};


%% 5) Grid Search
fprintf('\n--- Inizio Grid Search Manuale ---\n');
for i = 1:numel(classifiers)  % itera sui tipi di kernel
    clf = classifiers{i};     %estre il nome del kernel
    fprintf('\nValutazione Classificatore: %s\n', upper(clf));

    for ks = kernel_scales
        for bc = box_constraints
            fprintf('  Testando KernelScale=%.2f, BoxConstraint=%.2f...\n', ks, bc);

            % Cross-validation con k-fold
            cv = cvpartition(Y_trainval, "KFold", k_fold, 'Stratify', true);
            val_acc_fold = zeros(k_fold,1);

            for fold = 1:k_fold
                train_idx = training(cv, fold);
                val_idx   = test(cv, fold);

                X_fold_train = X_trainval(train_idx, :);
                Y_fold_train = Y_trainval(train_idx);
                X_fold_val   = X_trainval(val_idx, :);
                Y_fold_val   = Y_trainval(val_idx);

                % Selezione del kernel
                if strcmp(clf, 'rbf') 
                    kernel_function = 'rbf';
                elseif strcmp(clf, 'linear') 
                    kernel_function = 'linear';
                else
                    error('Kernel non valido.'); 
                end

                % Addestramento del modello SVM
                svm_model = fitcsvm(X_fold_train, Y_fold_train, ...
                    'Standardize', false, ...
                    'BoxConstraint', bc, ...
                    'KernelFunction', kernel_function);
            
                
                Y_val_pred = predict(svm_model, X_fold_val);
                val_acc_fold(fold) = mean(Y_val_pred == Y_fold_val); % Accuratezza di validation del fold corrente
            end

            % Accuratezza media su tutti i fold sui dati di validation 
            mean_acc = mean(val_acc_fold); 
            fprintf('Val Acc: %.2f%%\n', mean_acc*100);
            
            % Aggiornamento modello migliore 
            field_name = ['svm_' clf];
            if mean_acc > best_val_accuracies.(field_name)
                best_val_accuracies.(field_name) = mean_acc;

                % Retrain su tutto trainval
                best_models.(field_name) = fitcsvm(X_trainval, Y_trainval, ...
                    'Standardize', false, ...
                    'BoxConstraint', bc, ...
                    'KernelScale', ks, ...
                    'KernelFunction', kernel_function);
                % Salvataggio combinazione iperparametri
                best_hyperparameters.(field_name) = struct('KernelScale', ks, 'BoxConstraint', bc);   
            end
        end
    end
end


%% 6) Confronto Finale sul Test Set
fprintf('CONFRONTO SUL TEST SET...\n');

y_pred_rbf = predict(best_models.svm_rbf, X_test);
y_pred_lin = predict(best_models.svm_linear, X_test);

acc_rbf = mean(y_pred_rbf == Y_test);
acc_lin = mean(y_pred_lin == Y_test);

metrics_best_rbf = evaluate_metrics(confusionmat(Y_test, y_pred_rbf));
metrics_best_lin = evaluate_metrics(confusionmat(Y_test, y_pred_lin));

fprintf('Accuracy RBF:    %.2f%%\n', acc_rbf*100);
fprintf('Accuracy Linear: %.2f%%\n', acc_lin*100);


%% 7) Selezione modello migliore in base al test set
if acc_rbf >= acc_lin
    final_model = best_models.svm_rbf;
    final_acc   = acc_rbf;
    final_metrics = metrics_best_rbf;
    selected_kernel = 'RBF';
    selected_hyperparams = best_hyperparameters.svm_rbf;
else
    final_model = best_models.svm_linear;
    final_acc   = acc_lin;
    final_metrics = metrics_best_lin;
    selected_kernel = 'Linear';
    selected_hyperparams = best_hyperparameters.svm_linear;
end


%% 8) Salvataggio ed output risultati finali
saveLearnerForCoder(final_model, 'best_svm_model_onlyFILT.mat');

% Mostra i risultati finali
fprintf('Classificatore selezionato: %s\n', selected_kernel); 
fprintf('Accuratezza finale sul test set: %.2f%%\n', final_acc * 100); 

fprintf('Migliori iperparametri: KernelScale=%.2f, BoxConstraint=%.2f\n', ...
    selected_hyperparams.KernelScale, selected_hyperparams.BoxConstraint); 

% Matrice di confusione finale
final_conf_matrix = confusionmat(Y_test, predict(final_model, X_test)); 
disp('Matrice di confusione finale:');
disp(final_conf_matrix); 

fprintf('Metriche finali sul test set:\n');
disp(final_metrics); 

%% Funzione per calcolare le metriche precision, recall e F1-score
function metrics = evaluate_metrics(conf_matrix)
    num_classes = size(conf_matrix, 1);
    precision = zeros(num_classes, 1);
    recall = zeros(num_classes, 1);
    f1 = zeros(num_classes, 1);

    for c = 1:num_classes
        tp = conf_matrix(c, c);
        fp = sum(conf_matrix(:, c)) - tp;
        fn = sum(conf_matrix(c, :)) - tp;
        precision(c) = tp / (tp + fp + eps);
        recall(c) = tp / (tp + fn + eps);
        f1(c) = 2 * (precision(c) * recall(c)) / (precision(c) + recall(c) + eps);
    end

    metrics = table(mean(precision), mean(recall), mean(f1), ...
        'VariableNames', {'Precision', 'Recall', 'F1_Score'});
end