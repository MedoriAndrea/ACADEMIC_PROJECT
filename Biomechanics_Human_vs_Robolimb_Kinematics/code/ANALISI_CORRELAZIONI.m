% =========================================================================
% ANALISI DI CORRELAZIONE (Solo dataset Umano) - Separato per Condizione
% =========================================================================
clc; clear; close all;

fprintf('Caricamento Tabella Statistica...\n');
if ~exist('TabellaStatistica_Completa.mat', 'file')
    error('File TabellaStatistica_Completa.mat non trovato.');
end
load('TabellaStatistica_Completa.mat', 'TabellaStatistica');

% Selezioniamo SOLO i dati umani
datiUmani = TabellaStatistica(TabellaStatistica.Gruppo == 'Human', :);

% Le 11 metriche da incrociare
metriche = {'RoM_MCP', 'Movement_Time', 'Path_Length_Norm', ...
            'Linearity_Index', 'Bounding_Box_Area', 'V_Max', ...
            'Time_Plateau_95', 'SPARC_Fluidity', ...
            'Efficienza_Profilo_Velocita', 'Skewness_Profilo_Velocita', 'FWHM_Campana_Velocita'};

nomiPuliti = strrep(metriche, '_', ' ');
condizioni = unique(datiUmani.Condizione);

% --- CREAZIONE COLORMAP PERSONALIZZATA (Blu -> Bianco -> Rosso) ---
n = 128;
blu_bianco = [linspace(0, 1, n)', linspace(0, 1, n)', ones(n, 1)];
bianco_rosso = [ones(n, 1), linspace(1, 0, n)', linspace(1, 0, n)'];
customColorMap = [blu_bianco; bianco_rosso];

for c = 1:length(condizioni)
    condCorrente = condizioni(c);
    fprintf('\n======================================================\n');
    fprintf('>>> CONDIZIONE SPERIMENTALE: %s\n', char(condCorrente));
    fprintf('======================================================\n');
    
    % Filtriamo i dati umani SOLO per la condizione corrente
    datiCond = datiUmani(datiUmani.Condizione == condCorrente, :);
    matriceDati = datiCond{:, metriche};
    
    % Calcolo Pearson
    [R, ~] = corrcoef(matriceDati, 'Rows', 'complete');
    
    % Maschera per triangolo superiore
    maschera = logical(tril(ones(size(R)))); 
    R(maschera) = NaN; 
    
    % Creazione Figura Indipendente4.1 Descrizione del Dataset e Integrità dei Dati
    figName = sprintf('Correlazione Umana - %s', char(condCorrente));
    figure('Name', figName, 'Color', 'w', 'Position', [100 + (c*50), 100 + (c*50), 950, 750]);
    
    h = heatmap(nomiPuliti, nomiPuliti, R, 'ColorLimits', [-1 1]);
    h.Title = sprintf('Matrice di Correlazione (Umani) - Task: %s', char(condCorrente));
    h.Colormap = customColorMap;
    h.MissingDataColor = 'w'; 
    h.FontSize = 10;
    h.MissingDataLabel = '';  
    
    % Check in Console
    fprintf('>>> ALLARMI MULTICOLLINEARITA'' (|R| > 0.85)\n');
    trovate = false;
    for i = 1:length(metriche)
        for j = (i+1):length(metriche) 
            if abs(R(i,j)) > 0.85
                fprintf('- ATTENZIONE: %s e %s (R = %.2f)\n', nomiPuliti{i}, nomiPuliti{j}, R(i,j));
                trovate = true;
            end
        end
    end
    
    if ~trovate
        fprintf('- Nessuna correlazione critica (Variabili indipendenti).\n');
    end
end
fprintf('\n======================================================\n');


% =========================================================================
% 2. FASE DI PULIZIA AUTOMATICA (DOPPIO CONTROLLO SULLE CONDIZIONI)
% =========================================================================
fprintf('\n======================================================\n');
fprintf('>>> RIMOZIONE AUTOMATICA (LOGICA DEL DOPPIO CONTROLLO)\n');
fprintf('======================================================\n');

soglia_R = 0.90; 
TabellaStatistica_Pulita = TabellaStatistica;
feature_da_rimuovere = {};

% Prepariamo le matrici R per ogni condizione per non ricalcolarle
R_condizioni = cell(length(condizioni), 1);
for c = 1:length(condizioni)
    datiCond = datiUmani(datiUmani.Condizione == condizioni(c), :);
    matriceDati = datiCond{:, metriche};
    [R_condizioni{c}, ~] = corrcoef(matriceDati, 'Rows', 'complete');
end

% Scansioniamo le feature incrociandole
for i = 1:length(metriche)
    for j = (i+1):length(metriche)
        
        ridondante_ovunque = true; % Partiamo dal presupposto che lo sia
        valori_R = zeros(length(condizioni), 1);
        
        % Controlliamo se supera la soglia in TUTTE le condizioni
        for c = 1:length(condizioni)
            valori_R(c) = abs(R_condizioni{c}(i,j));
            if valori_R(c) < soglia_R
                ridondante_ovunque = false; % Si è "salvata" in almeno una condizione!
            end
        end
        
        % Se ha superato la soglia ovunque, procediamo all'eliminazione
        if ridondante_ovunque
            feat1 = metriche{i};
            feat2 = metriche{j};
            
            if ~ismember(feat1, feature_da_rimuovere) && ~ismember(feat2, feature_da_rimuovere)
                feature_da_rimuovere{end+1} = feat2;
                fprintf('- Rilevata correlazione persistente in tutte le condizioni:\n');
                for c = 1:length(condizioni)
                    fprintf('  [%s] |R| = %.2f\n', char(condizioni(c)), valori_R(c));
                end
                fprintf('  -> Mantengo: [%s]\n', strrep(feat1, '_', ' '));
                fprintf('  -> Scarto:   [%s]\n\n', strrep(feat2, '_', ' '));
            end
        end
        
    end
end

% Eliminazione fisica
if isempty(feature_da_rimuovere)
    fprintf('- Nessuna variabile è risultata ridondante in TUTTE le condizioni. Non elimino nulla.\n');
else
    for k = 1:length(feature_da_rimuovere)
        if ismember(feature_da_rimuovere{k}, TabellaStatistica_Pulita.Properties.VariableNames)
            TabellaStatistica_Pulita.(feature_da_rimuovere{k}) = []; 
        end
    end
    fprintf('- Pulizia terminata. %d feature eliminate.\n', length(feature_da_rimuovere));
end

save('TabellaStatistica_Pulita.mat', 'TabellaStatistica_Pulita');
fprintf('\n>>> TabellaStatistica_Pulita.mat salvata correttamente!\n');