% =========================================================================
% SCRIPT DI VISUALIZZAZIONE: Traiettorie Reali e Normalizzate
% =========================================================================

clc; clear; close all;

% Caricamento dei dati elaborati
load('dataset_biomeccanico_elaborato.mat', 'datasetElaborato');

% Estraiamo le condizioni disponibili (assumendo che Human sia la reference)
if isfield(datasetElaborato, 'Human')
    condizioniDisponibili = fieldnames(datasetElaborato.Human);
else
    error('Nessun dato Human trovato nel dataset.');
end

% Colore fisso per il Robot (es. un Rosso scuro e spesso per farlo risaltare)
coloreRobot = [0.8500, 0.1250, 0.0980]; 

% Ciclo su tutte le condizioni (LIBERA, BIDIGITALE, ecc.)
for c = 1:length(condizioniDisponibili)
    condizione = condizioniDisponibili{c};
    
    % Creazione delle due figure separate
    figRaw = figure('Name', sprintf('Reali (cm) - %s', condizione), 'Color', 'w', 'Position', [100, 100, 700, 500]);
    hold on; grid on; axis equal;
    title(sprintf('Traiettorie Assolute (cm) - Condizione: %s', condizione), 'FontSize', 12);
    xlabel('Asse X Locale (cm)', 'FontSize', 11);
    ylabel('Asse Y Locale (cm)', 'FontSize', 11);
    
    figNorm = figure('Name', sprintf('Normalizzate - %s', condizione), 'Color', 'w', 'Position', [820, 100, 700, 500]);
    hold on; grid on; axis equal;
    title(sprintf('Traiettorie Normalizzate (X/L) - Condizione: %s', condizione), 'FontSize', 12);
    xlabel('Asse X Normalizzato', 'FontSize', 11);
    ylabel('Asse Y Normalizzato', 'FontSize', 11);
    
    % --- PLOT HUMAN (Colori dinamici per ogni soggetto) ---
    soggettiUmani = fieldnames(datasetElaborato.Human.(condizione));
    numUmani = length(soggettiUmani);
    
    % Generazione automatica di colori distinti per ogni soggetto umano
    paletteColori = lines(numUmani); 
    
    % Array per salvare gli handle dei plot per la legenda (1 per soggetto)
    handlesLegendaRaw = [];  nomiLegendaRaw = {};
    handlesLegendaNorm = []; nomiLegendaNorm = {};
    
    for s = 1:numUmani
        soggetto = soggettiUmani{s};
        coloreSoggetto = paletteColori(s, :); % Colore unico per questo soggetto
        
        trials = fieldnames(datasetElaborato.Human.(condizione).(soggetto));
        handleSoggettoRaw = [];
        handleSoggettoNorm = [];
        
        for t = 1:length(trials)
            trial = trials{t};
            
            % Estrazione dati grezzi
            X_raw = datasetElaborato.Human.(condizione).(soggetto).(trial).TIP_Local_X;
            Y_raw = datasetElaborato.Human.(condizione).(soggetto).(trial).TIP_Local_Y;
            L_ind = datasetElaborato.Human.(condizione).(soggetto).(trial).L_indice;
            
            % Filtraggio zeri (frame persi/tracking fallito)
            validIdx = (X_raw ~= 0) & (Y_raw ~= 0);
            X_raw = X_raw(validIdx);
            Y_raw = Y_raw(validIdx);
            
            % Calcolo normalizzazione
            X_norm = X_raw / L_ind;
            Y_norm = Y_raw / L_ind;
            
            % Plot Figura Reale
            figure(figRaw);
            pRaw = plot(X_raw, Y_raw, '-', 'Color', [coloreSoggetto, 0.4], 'LineWidth', 1.5);
            if isempty(handleSoggettoRaw), handleSoggettoRaw = pRaw; end % Salva il primo per la legenda
            
            % Plot Figura Normalizzata
            figure(figNorm);
            pNorm = plot(X_norm, Y_norm, '-', 'Color', [coloreSoggetto, 0.4], 'LineWidth', 1.5);
            if isempty(handleSoggettoNorm), handleSoggettoNorm = pNorm; end
        end
        
        % Salvataggio legenda per il soggetto umano corrente
        handlesLegendaRaw(end+1) = handleSoggettoRaw;
        nomiLegendaRaw{end+1} = sprintf('Umano: %s', soggetto);
        handlesLegendaNorm(end+1) = handleSoggettoNorm;
        nomiLegendaNorm{end+1} = sprintf('Umano: %s', soggetto);
    end
    
    % --- PLOT ROBOT ---
    if isfield(datasetElaborato, 'Robot') && isfield(datasetElaborato.Robot, condizione)
        soggettiRobot = fieldnames(datasetElaborato.Robot.(condizione));
        handleRobotRaw = []; handleRobotNorm = [];
        
        for s = 1:length(soggettiRobot)
            soggettoR = soggettiRobot{s};
            trialsR = fieldnames(datasetElaborato.Robot.(condizione).(soggettoR));
            
            for t = 1:length(trialsR)
                trialR = trialsR{t};
                
                % Dati Robot
                X_raw = datasetElaborato.Robot.(condizione).(soggettoR).(trialR).TIP_Local_X;
                Y_raw = datasetElaborato.Robot.(condizione).(soggettoR).(trialR).TIP_Local_Y;
                L_ind = datasetElaborato.Robot.(condizione).(soggettoR).(trialR).L_indice;
                
                validIdx = (X_raw ~= 0) & (Y_raw ~= 0);
                X_raw = X_raw(validIdx); Y_raw = Y_raw(validIdx);
                X_norm = X_raw / L_ind;  Y_norm = Y_raw / L_ind;
                
                % Plot Raw Robot
                figure(figRaw);
                pRawR = plot(X_raw, Y_raw, '-', 'Color', [coloreRobot, 0.8], 'LineWidth', 2.5);
                if isempty(handleRobotRaw), handleRobotRaw = pRawR; end
                
                % Plot Norm Robot
                figure(figNorm);
                pNormR = plot(X_norm, Y_norm, '-', 'Color', [coloreRobot, 0.8], 'LineWidth', 2.5);
                if isempty(handleRobotNorm), handleRobotNorm = pNormR; end
            end
        end
        
        if ~isempty(handleRobotRaw)
            handlesLegendaRaw(end+1) = handleRobotRaw;
            nomiLegendaRaw{end+1} = 'Robolimb';
            handlesLegendaNorm(end+1) = handleRobotNorm;
            nomiLegendaNorm{end+1} = 'Robolimb';
        end
    end
    
    % --- ORIGINE E LEGEND COMPLETA ---
    figure(figRaw);
    pOrig = plot(0, 0, 'ko', 'MarkerFaceColor', 'k', 'MarkerSize', 8);
    legend([pOrig, handlesLegendaRaw], [{'MCP (Origine)'}, nomiLegendaRaw], 'Location', 'best');
    hold off;
    
    figure(figNorm);
    pOrigN = plot(0, 0, 'ko', 'MarkerFaceColor', 'k', 'MarkerSize', 8);
    legend([pOrigN, handlesLegendaNorm], [{'MCP (Origine)'}, nomiLegendaNorm], 'Location', 'best');
    hold off;
end