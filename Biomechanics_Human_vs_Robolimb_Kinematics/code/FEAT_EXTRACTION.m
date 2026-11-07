% =========================================================================
% ESTRAZIONE FEATURE COMPLETE E RIMOZIONE OUTLIER
% =========================================================================
clc; clear; close all;

% Caricamento del dataset
fprintf('Caricamento dataset...\n');
load('dataset_biomeccanico_elaborato.mat', 'datasetElaborato');

% Inizializzazione array per la Tabella Statistica
Gruppo = {}; Condizione = {}; Soggetto = {}; Trial_ID = {};
RoM_MCP = []; Path_Length_Norm = []; Linearity_Index = []; 
Bounding_Box_Area = []; V_Max = []; Movement_Time = []; 
Time_Plateau_95 = []; SPARC_Fluidity = [];
% --- NUOVE METRICHE ---
Efficienza_Profilo_Velocita = []; Skewness_Profilo_Velocita = []; FWHM_Campana_Velocita = [];

% Frequenza di campionamento stimata (30 fps) e design del filtro
fs = 30; 
fc = 5; % Frequenza di taglio passa-basso a 5 Hz
[b, a] = butter(2, fc/(fs/2), 'low'); % Filtro Butterworth 2° ordine

categorie = fieldnames(datasetElaborato);
for c = 1:length(categorie)
    catName = categorie{c};
    condizioni = fieldnames(datasetElaborato.(catName));
    
    for condIdx = 1:length(condizioni)
        condName = condizioni{condIdx};
        soggetti = fieldnames(datasetElaborato.(catName).(condName));
        
        for sIdx = 1:length(soggetti)
            sogName = soggetti{sIdx};
            trials = fieldnames(datasetElaborato.(catName).(condName).(sogName));
            
            for tIdx = 1:length(trials)
                trialName = trials{tIdx};
                
                % Estrazione dati grezzi
                angoli = datasetElaborato.(catName).(condName).(sogName).(trialName).MCP_Angle;
                X_cm = datasetElaborato.(catName).(condName).(sogName).(trialName).TIP_Local_X;
                Y_cm = datasetElaborato.(catName).(condName).(sogName).(trialName).TIP_Local_Y;
                V_tot = datasetElaborato.(catName).(condName).(sogName).(trialName).TIP_Vtot;
                L_ind = datasetElaborato.(catName).(condName).(sogName).(trialName).L_indice;
                
                % Filtraggio base per zeri e normalizzazione spaziale
                validIdx = (X_cm ~= 0) & (Y_cm ~= 0);
                if sum(validIdx) < 15
                    continue; % Salta i trial troppo corti o corrotti
                end
                
                angoli = angoli(validIdx);
                X_norm = X_cm(validIdx) / L_ind;
                Y_norm = Y_cm(validIdx) / L_ind;
                V_tot = V_tot(validIdx);
                
                % 1. FILTRAGGIO (Butterworth)
                V_filt = filtfilt(b, a, V_tot);

                
                % 2. FINESTRA DINAMICA (ONSET E OFFSET)
                v_picco = max(V_filt);
                soglia_movimento = 0.05 * v_picco; % 5% della Vmax
                
                idx_movimento = find(V_filt > soglia_movimento);
                if isempty(idx_movimento)
                    continue;
                end
                
                idx_start = idx_movimento(1);
                idx_end = idx_movimento(end);
                
                % Ritaglio dei dati sulla finestra "attiva"
                angoli_act = angoli(idx_start:idx_end);
                X_act = X_norm(idx_start:idx_end);
                Y_act = Y_norm(idx_start:idx_end);
                V_act = V_filt(idx_start:idx_end);
                
                % --- CALCOLO DELLE FEATURE SULLA FINESTRA ATTIVA ---
                
                mov_time = (idx_end - idx_start) / fs;
                rom_mcp = max(angoli_act) - min(angoli_act);
                
                dX = diff(X_act); dY = diff(Y_act);
                path_len_norm = sum(sqrt(dX.^2 + dY.^2));
                
                distanza_retta = sqrt((X_act(end) - X_act(1))^2 + (Y_act(end) - Y_act(1))^2);
                lin_index = distanza_retta / path_len_norm;
                
                bbox_area = (max(X_act) - min(X_act)) * (max(Y_act) - min(Y_act));
                vmax_act = max(V_act);
                
                idx_95 = find(V_act >= 0.95 * vmax_act);
                time_95 = length(idx_95) / fs; 
                
                sparc_val = compute_SPARC(V_act, fs);
                
                % --- NUOVI DESCRITTORI DI FORMA DEL PROFILO ---
                % 1. EFFICIENZA DEL PROFILO (V_mean / V_max)
                efficienza_val = mean(V_act) / vmax_act;
                
                % 2. ASIMMETRIA (Skewness)
                skewness_val = skewness(V_act);
                
                % 3. APERTURA DELLA CAMPANA (FWHM)
                idx_50 = find(V_act >= 0.5 * vmax_act);
                if ~isempty(idx_50)
                    fwhm_val = (idx_50(end) - idx_50(1)) / fs;
                else
                    fwhm_val = NaN;
                end
                
                % --- SALVATAGGIO IN STRUTTURA ---
                Gruppo{end+1, 1} = catName;
                Condizione{end+1, 1} = condName;
                Soggetto{end+1, 1} = sogName;
                Trial_ID{end+1, 1} = trialName;
                RoM_MCP(end+1, 1) = rom_mcp;
                Path_Length_Norm(end+1, 1) = path_len_norm;
                Linearity_Index(end+1, 1) = lin_index;
                Bounding_Box_Area(end+1, 1) = bbox_area;
                V_Max(end+1, 1) = vmax_act;
                Movement_Time(end+1, 1) = mov_time;
                Time_Plateau_95(end+1, 1) = time_95;
                SPARC_Fluidity(end+1, 1) = sparc_val;
                Efficienza_Profilo_Velocita(end+1, 1) = efficienza_val;
                Skewness_Profilo_Velocita(end+1, 1) = skewness_val;
                FWHM_Campana_Velocita(end+1, 1) = fwhm_val;
            end
        end
    end
end

% Creazione Tabella Iniziale
TabellaStatistica = table(Gruppo, Condizione, Soggetto, Trial_ID, ...
    RoM_MCP, Movement_Time, Path_Length_Norm, Linearity_Index, ...
    Bounding_Box_Area, V_Max, Time_Plateau_95, SPARC_Fluidity, ...
    Efficienza_Profilo_Velocita, Skewness_Profilo_Velocita, FWHM_Campana_Velocita);

% FONDAMENTALE: Trasformazione in Categorical PRIMA degli outlier
TabellaStatistica.Gruppo = categorical(TabellaStatistica.Gruppo);
TabellaStatistica.Condizione = categorical(TabellaStatistica.Condizione);

% =========================================================================
% RIMOZIONE OUTLIER (PULIZIA DATI INTELLIGENTE PER TUTTI)
% =========================================================================
fprintf('\n>>> Identificazione e rimozione Outlier (Trial Corrotti)...\n');
idx_outlier_totali = false(height(TabellaStatistica), 1);

gruppi = unique(TabellaStatistica.Gruppo);
condizioni_uniche = unique(TabellaStatistica.Condizione);

% Identifichiamo i nomi delle colonne numeriche (dalla 5 in poi)
metriche_num = TabellaStatistica.Properties.VariableNames(5:end);

for g = 1:length(gruppi)
    nome_gruppo = char(gruppi(g));
    
    % Impostiamo la soglia di tolleranza (Regola del Consenso)
    % Un trial viene scartato SOLO se è anomalo in almeno 3 feature diverse.
    % Questo intercetta i veri glitch di tracking (es. marker occluso) che 
    % fanno sballare V_Max, Path Length e SPARC tutte insieme.
    soglia_anomalie = 3; 
    
    for c = 1:length(condizioni_uniche)
        % Maschera per isolare il gruppo e la condizione specifica (es. Robot - Libera)
        maschera = (TabellaStatistica.Gruppo == gruppi(g)) & (TabellaStatistica.Condizione == condizioni_uniche(c));
        
        if sum(maschera) > 0
            dati_subset = TabellaStatistica{maschera, metriche_num};
            
            % isoutlier con metodo 'quartiles' (identifica valori oltre 1.5 IQR)
            % Il confronto avviene STRETTAMENTE all'interno del proprio set
            outliers_matrice = isoutlier(dati_subset, 'quartiles');
            
            % Il trial è da scartare solo se la somma delle anomalie >= soglia
            trial_da_scartare = sum(outliers_matrice, 2) >= soglia_anomalie;
            
            % Registriamo nell'indice globale della tabella
            idx_locali = find(maschera);
            idx_outlier_totali(idx_locali(trial_da_scartare)) = true;
        end
    end
end

num_scartati = sum(idx_outlier_totali);
fprintf('- Trovati %d veri trial corrotti su %d totali.\n', num_scartati, height(TabellaStatistica));

% --- STAMPA DEL DETTAGLIO DEI TRIAL ELIMINATI ---
if num_scartati > 0
    fprintf('\n--- REGISTRO ELIMINAZIONI (OUTLIER GRAVI) ---\n');
    tabelle_scartati = TabellaStatistica(idx_outlier_totali, {'Gruppo', 'Condizione', 'Soggetto', 'Trial_ID'});
    for k = 1:height(tabelle_scartati)
        fprintf('Scartato -> Gruppo: %s | Condizione: %s | Soggetto: %s | Trial: %s\n', ...
            char(tabelle_scartati.Gruppo(k)), ...
            char(tabelle_scartati.Condizione(k)), ...
            char(tabelle_scartati.Soggetto(k)), ...
            char(tabelle_scartati.Trial_ID(k)));
    end
    fprintf('-----------------------------------------------\n\n');
end

% Eliminazione fisica delle righe schifose
TabellaStatistica(idx_outlier_totali, :) = [];
fprintf('- Rimozione completata. Trial puliti rimanenti: %d.\n', height(TabellaStatistica));

% Salvataggio Finale Unico
save('TabellaStatistica_Completa.mat', 'TabellaStatistica');
fprintf('\n>>> Estrazione completata! Tabella salvata in TabellaStatistica_Completa.mat\n');
% -------------------------------------------------------------------------
% SOTTO-FUNZIONE: Calcolo SPARC
% -------------------------------------------------------------------------
function sparc_index = compute_SPARC(v, fs)
    v = v - mean(v);
    N = length(v);
    V_fft = fft(v);
    V_amp = abs(V_fft(1:floor(N/2))) / N; 
    
    freqs = (0:floor(N/2)-1)' * (fs / N);
    fc_sparc = 10; 
    idx_fc = find(freqs <= fc_sparc);
    
    if isempty(idx_fc) || max(V_amp) == 0
        sparc_index = NaN; return;
    end
    
    V_amp = V_amp(idx_fc);
    freqs = freqs(idx_fc);
    V_amp_norm = V_amp / max(V_amp);
    
    df = freqs(2) - freqs(1);
    dV = diff(V_amp_norm);
    arc_length = sum(sqrt(df^2 + dV.^2));
    sparc_index = -arc_length;
end