% =========================================================================
% ANALISI STATISTICA HEATMAP (Con logica Kruskal-Wallis e Gruppo Globale)
% =========================================================================
clc; clear; close all;

fprintf('Caricamento Tabella Statistica Pulita...\n');
if ~exist('TabellaStatistica_Pulita.mat', 'file')
    error('File TabellaStatistica_Pulita.mat non trovato.');
end
load('TabellaStatistica_Pulita.mat', 'TabellaStatistica_Pulita');

% 1. IDENTIFICAZIONE AUTOMATICA DELLE METRICHE
% --- AGGIUNTO 'Trial_ID' ALLA LISTA DELLE COLONNE DA ESCLUDERE ---
colonne_escluse = {'Soggetto', 'Condizione', 'Trial', 'Gruppo', 'Nome_Video', 'Trial_ID'};
metriche = setdiff(TabellaStatistica_Pulita.Properties.VariableNames, colonne_escluse, 'stable');
nomiMetrichePuliti = strrep(metriche, '_', ' ');
condizioni = unique(TabellaStatistica_Pulita.Condizione);

% Colormap per il p-value (Rosso < 0.05, Verde > 0.05)
cmap_pvalue = [repmat([0.85 0.2 0.2], 5, 1); repmat([0.2 0.8 0.2], 95, 1)];

for c = 1:length(condizioni)
    condCorrente = condizioni(c);
    fprintf('\n======================================================\n');
    fprintf('>>> MAPPA STATISTICA (KW integrato): %s\n', char(condCorrente));
    fprintf('======================================================\n');
    
    datiCond = TabellaStatistica_Pulita(TabellaStatistica_Pulita.Condizione == condCorrente, :);
    idxHuman = datiCond.Gruppo == 'Human';
    idxRobot = datiCond.Gruppo == 'Robot';
    
    datiUmani = datiCond(idxHuman, :);
    datiRobot = datiCond(idxRobot, :);
    
    nomiUmani = unique(datiUmani.Soggetto);
    numUmani = length(nomiUmani);
    
    % Creiamo le etichette per l'asse X aggiungendo la colonna Globale
    etichetteX = [nomiUmani; {'Gruppo Globale'}];
    
    % Matrice per salvare i p-value (inizializzata a NaN per renderli trasparenti)
    % Colonne = numUmani + 1 (l'ultima è per il globale)
    matrice_p = NaN(length(metriche), numUmani + 1);
    
    % --- ESECUZIONE DEI TEST STATISTICI ---
    for m = 1:length(metriche)
        metrica = metriche{m};
        
        % 1. Estrazione dati grezzi
        rawH = datiUmani.(metrica);
        rawR = datiRobot.(metrica);
        
        % 2. Conversione di sicurezza: se sono 'cell', li spacchetta in numeri
        if iscell(rawH)
            try rawH = cell2mat(rawH); catch, continue; end
        end
        if iscell(rawR)
            try rawR = cell2mat(rawR); catch, continue; end
        end
        
        % 3. Sicurezza extra: se non sono numeri, salta la colonna
        if ~isnumeric(rawH) || ~isnumeric(rawR)
            continue;
        end
        
        % 4. Pulizia dei NaN 
        validH = ~isnan(rawH);
        validR = ~isnan(rawR);
        
        valHuman = rawH(validH);
        soggettiHuman = datiUmani.Soggetto(validH);
        valRobot = rawR(validR);
        
        % Se non ci sono dati sufficienti dopo la pulizia, passa alla prossima metrica
        if isempty(valHuman) || isempty(valRobot)
            continue;
        end
        
        % 5. Test di Kruskal-Wallis (Il "Bivio")
        p_kw = kruskalwallis(valHuman, soggettiHuman, 'off');
        
        if p_kw > 0.05
            % --- CASO A: Umani Omogenei (Test Globale) ---
            p_val_globale = ranksum(valHuman, valRobot);
            matrice_p(m, end) = p_val_globale; % Salva nell'ultima colonna
        else
            % --- CASO B: Umani Eterogenei (Test 1-vs-1) ---
            for s = 1:numUmani
                % Correzione applicata: utilizzo di strcmp per i cell array di stringhe
                valSoggetto = valHuman(strcmp(soggettiHuman, nomiUmani{s}));
                if ~isempty(valSoggetto)
                    p_val_singolo = ranksum(valSoggetto, valRobot);
                    matrice_p(m, s) = p_val_singolo; % Salva nelle colonne singole
                end
            end
        end
    end
    
    % --- VISUALIZZAZIONE HEATMAP ---
    figName = sprintf('Risultati Statistici - %s', char(condCorrente));
    figure('Name', figName, 'Color', 'w', 'Position', [100 + (c*50), 100 + (c*50), 750, 600]);
    
    h = heatmap(etichetteX, nomiMetrichePuliti, matrice_p);
    h.Title = sprintf('Confronto Robolimb vs Umani - %s', char(condCorrente));
    h.XLabel = 'Soggetti e Raggruppamento (KW)';
    h.YLabel = 'Feature Cinematiche';
    
    h.Colormap = cmap_pvalue;
    h.ColorLimits = [0 1];
    h.CellLabelFormat = '%.3f'; 
    
    % Le caselle vuote (dove il test non è stato applicato) diventano grigio chiaro
    h.MissingDataColor = [0.95 0.95 0.95];
    h.MissingDataLabel = '-';
    h.FontSize = 11;
end
fprintf('\n>>> Analisi completata e Heatmap generate con successo!\n');

Tabella_Pulita_Bidigitale = TabellaStatistica_Pulita(TabellaStatistica_Pulita.Condizione == 'BIDIGITALE', :);

% Prende tutte le righe in cui Condizione è uguale a 'LIBERA' (e tutte le colonne ':')
Tabella_Pulita_Libera = TabellaStatistica_Pulita(TabellaStatistica_Pulita.Condizione == 'LIBERA', :);