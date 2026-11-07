%% PCA con selezione automatica delle componenti + plot

TARGET_VAR = 95;   % <-- soglia di varianza cumulata (%)

%% 1) Pulizia righe non valide
bad = any(~isfinite(X), 2);
if any(bad)
    warning("Rimosse %d righe con NaN/Inf.", sum(bad));
    X = X(~bad,:);
    if exist("y","var") && ~isempty(y)
        y = y(~bad);
    end
end

%% 2) Standardizzazione + PCA
X_std = zscore(X);
[coeff, score, latent, tsquared, explained] = pca(X_std);

%% 3) Numero di componenti per TARGET_VAR%
cum_explained = cumsum(explained);
k = find(cum_explained >= TARGET_VAR, 1, 'first');
if isempty(k)
    k = numel(explained);
end

fprintf("Per raggiungere almeno %.1f%% di varianza servono k = %d componenti.\n", ...
        TARGET_VAR, k);

X_reduced   = score(:, 1:k);
explained_k = explained(1:k);


%% PLOT 1 — Scree Plot

figure;
plot(explained, 'o-', 'LineWidth', 1.5);
grid on;
xlabel('Componente Principale');
ylabel('Varianza spiegata (%)');
title('Scree Plot – Varianza spiegata per PC');


%% PLOT 2 — Varianza cumulata
figure;
plot(cum_explained, 'o-', 'LineWidth', 1.5); hold on;
yline(TARGET_VAR, '--r', 'Target', 'LineWidth', 1.2);
xline(k, '--k', 'k selezionato', 'LineWidth', 1.2);
grid on;
xlabel('Numero Componenti');
ylabel('Varianza cumulata (%)');
title('Varianza cumulata e selezione automatica di k');
hold off;

%% PLOT 3 — PC1 vs PC2

if size(score,2) >= 2
    figure;
    if exist("y","var") && ~isempty(y)
        gscatter(score(:,1), score(:,2), categorical(y), [], '.', 10);
        legend('Location','best');
    else
        scatter(score(:,1), score(:,2), 15, 'filled');
    end
    grid on;
    xlabel(sprintf('PC1 (%.1f%%)', explained(1)));
    ylabel(sprintf('PC2 (%.1f%%)', explained(2)));
    title('Score Plot: PC1 vs PC2');
end

%% PLOT 4 — PC1 vs PC2 vs PC3 (3D)

if size(score,2) >= 3
    figure;
    if exist("y","var") && ~isempty(y)
        labels_cat = categorical(y);
        groups = categories(labels_cat);
        hold on;
        for g = 1:numel(groups)
            idx = labels_cat == groups{g};
            scatter3(score(idx,1), score(idx,2), score(idx,3), ...
                     40, '.', 'DisplayName', groups{g});
        end
        legend('Location','best');
        hold off;
    else
        scatter3(score(:,1), score(:,2), score(:,3), 20, 'filled');
    end
    grid on;
    xlabel(sprintf('PC1 (%.1f%%)', explained(1)));
    ylabel(sprintf('PC2 (%.1f%%)', explained(2)));
    zlabel(sprintf('PC3 (%.1f%%)', explained(3)));
    title('Score Plot 3D: PC1 vs PC2 vs PC3');
    view(3);
end
save('features_e_pca.mat', 'X', 'feature_names', 'X_reduced', 'k', 'coeff', 'explained','y');