% =========================================================================
% ANALISI STATISTICA: Confronto Diretto Condizioni (SOLO BOXPLOT)
% =========================================================================
clc; clear; close all;

fprintf('Caricamento Tabella Statistica Pulita...\n');
if ~exist('TabellaStatistica_Pulita.mat', 'file')
    error('File TabellaStatistica_Pulita.mat non trovato. Esegui prima lo script di pulizia.');
end
load('TabellaStatistica_Pulita.mat', 'TabellaStatistica_Pulita');
TabellaStatistica = TabellaStatistica_Pulita; 

% 1. IDENTIFICAZIONE DELLE METRICHE (Esplicita e Sicura)
% Elenchiamo solo le feature biomeccaniche reali
tutte_le_metriche = {'RoM_MCP', 'Movement_Time', 'Path_Length_Norm', ...
            'Linearity_Index', 'Bounding_Box_Area', 'V_Max', ...
            'Time_Plateau_95', 'SPARC_Fluidity', ...
            'Efficienza_Profilo_Velocita', 'Skewness_Profilo_Velocita', 'FWHM_Campana_Velocita'};

% Intersechiamo l'elenco con le colonne effettivamente presenti nella tabella pulita
metriche = intersect(TabellaStatistica.Properties.VariableNames, tutte_le_metriche, 'stable');

% Fissiamo l'ordine delle condizioni per avere sempre Libera a sx e Bidigitale a dx
condizioni_plot = {'LIBERA', 'BIDIGITALE'};

% 2. CICLO SULLE METRICHE (Creazione Figure)
for m = 1:length(metriche)
    metrica = metriche{m};
    nomeMetricaPulito = strrep(metrica, '_', ' ');
    
    fprintf('\n======================================================\n');
    fprintf('>>> Analisi Metrica: %s\n', nomeMetricaPulito);
    fprintf('======================================================\n');
    
    % Creazione Figura per la metrica corrente
    figName = sprintf('Confronto Condizioni - %s', nomeMetricaPulito);
    figure('Name', figName, 'Color', 'w', 'Position', [100, 100, 1200, 600]);
    
    % =====================================================================
    % TILEDLAYOUT (Sostituisce il vecchio subplot)
    % =====================================================================
    t = tiledlayout(1, 2, 'TileSpacing', 'normal', 'Padding', 'normal');
    title(t, sprintf('Impatto del Task: %s', nomeMetricaPulito), 'FontSize', 16, 'FontWeight', 'bold');
    
    % Inizializzo un array per salvare gli "handle" (identificatori)
    h_ax = gobjects(1, 2);
    
    % CICLO SULLE CONDIZIONI
    for c = 1:2
        condCorrente = condizioni_plot{c};
        
        datiCond = TabellaStatistica(TabellaStatistica.Condizione == condCorrente, :);
        idxHuman = datiCond.Gruppo == 'Human';
        idxRobot = datiCond.Gruppo == 'Robot';
        
        % Estrazione grezza
        rawH = datiCond.(metrica)(idxHuman);
        rawR = datiCond.(metrica)(idxRobot);
        soggettiHumanRaw = datiCond.Soggetto(idxHuman);
        
        % Conversioni di sicurezza
        if iscell(rawH), try rawH = cell2mat(rawH); catch, continue; end; end
        if iscell(rawR), try rawR = cell2mat(rawR); catch, continue; end; end
        if ~isnumeric(rawH) || ~isnumeric(rawR), continue; end
        
        if iscategorical(soggettiHumanRaw)
            soggettiHuman = cellstr(soggettiHumanRaw);
        else
            soggettiHuman = soggettiHumanRaw;
        end
        
        % Pulizia NaN
        validH = ~isnan(rawH); validR = ~isnan(rawR);
        valHuman = rawH(validH); soggettiHuman = soggettiHuman(validH); valRobot = rawR(validR);
        
        if isempty(valHuman) || isempty(valRobot)
            h_ax(c) = nexttile; 
            title(sprintf('%s (Dati Insufficienti)', condCorrente));
            continue;
        end
        
        % -----------------------------------------------------------------
        % STATISTICA E BIVIO
        % -----------------------------------------------------------------
        nomiUmani = unique(soggettiHuman);
        numUmani = length(nomiUmani);
        p_1vs1 = NaN(numUmani, 1); 
        coloriUmani = lines(numUmani); 
        
        if numUmani > 1
            p_kw = kruskalwallis(valHuman, soggettiHuman, 'off');
            if p_kw > 0.05
                p_mw_plot = ranksum(valHuman, valRobot);
            else
                for s = 1:numUmani
                    val_sog = valHuman(strcmp(soggettiHuman, nomiUmani{s}));
                    if ~isempty(val_sog)
                        p_1vs1(s) = ranksum(val_sog, valRobot);
                    end
                end
                p_mw_plot = NaN; 
            end
        else
            p_mw_plot = ranksum(valHuman, valRobot);
        end
        
        % -----------------------------------------------------------------
        % DISEGNO DEL GRAFICO (SOLO BOXPLOT)
        % -----------------------------------------------------------------
        h_ax(c) = nexttile; 
        
        if ~isnan(p_mw_plot)
            % --- CASO A: UMANI OMOGENEI ---
            gruppi_plot = repmat({'Human'}, length(valHuman), 1);
            gruppi_plot = [gruppi_plot; repmat({'Robolimb'}, length(valRobot), 1)];
            dati_plot = [valHuman; valRobot];
            
            boxplot(dati_plot, gruppi_plot, 'Colors', 'k', 'Symbol', '');
            hold on; grid on;
            
            for s = 1:numUmani
                idx_sog = strcmp(soggettiHuman, nomiUmani{s});
                val_sog = valHuman(idx_sog);
                x_sog = ones(length(val_sog), 1) + (rand(length(val_sog), 1) - 0.5) * 0.15;
                plot(x_sog, val_sog, '.', 'Color', coloriUmani(s,:), 'MarkerSize', 15);
            end
            
            x_robot = 2 * ones(length(valRobot), 1) + (rand(length(valRobot), 1) - 0.5) * 0.15;
            plot(x_robot, valRobot, '.', 'Color', [0.85 0.1 0.1], 'MarkerSize', 15);
            
            if p_mw_plot < 0.05
                y_min = min([valHuman; valRobot]); 
                y_max = max([valHuman; valRobot]);
                y_range = y_max - y_min;
                y_ast = y_min - 0.5 * y_range; % Scende del 5% sotto il minimo
                
                plot([1 2], [y_ast y_ast], '-k', 'LineWidth', 1.5);
                text(1.5, y_ast - 0.02 * y_range, '*', 'FontSize', 22, 'HorizontalAlignment', 'center', 'Color', 'r', 'VerticalAlignment', 'top');
            end
            
            title(sprintf('%s\n(Umani Omogenei | Globale p = %.3f)', condCorrente, p_mw_plot), 'FontSize', 12);
            set(gca, 'XTickLabel', {'Human', 'Robolimb'});
            
        else

            % --- CASO B: UMANI ETEROGENEI ---
            X_all = [valHuman; valRobot];
            G_all = [soggettiHuman; repmat({'Robolimb'}, length(valRobot), 1)];
            ordine_gruppi = [nomiUmani; {'Robolimb'}];
            G_all = categorical(G_all, ordine_gruppi);
            
            boxplot(X_all, G_all, 'Colors', 'k', 'Symbol', '');
            hold on; grid on;
            
            for s = 1:numUmani
                val_sog = valHuman(strcmp(soggettiHuman, nomiUmani{s}));
                x_sog = s * ones(length(val_sog), 1) + (rand(length(val_sog), 1) - 0.5) * 0.15;
                plot(x_sog, val_sog, '.', 'Color', coloriUmani(s,:), 'MarkerSize', 15);
            end
            
            x_rob = (numUmani + 1) * ones(length(valRobot), 1) + (rand(length(valRobot), 1) - 0.5) * 0.15;
            plot(x_rob, valRobot, '.', 'Color', [0.85 0.1 0.1], 'MarkerSize', 15);
            
            med_rob = median(valRobot);
            plot([0.5, numUmani + 1.5], [med_rob, med_rob], '--', 'Color', [0.85 0.1 0.1 0.5], 'LineWidth', 1.5);
            
            y_max = max(X_all); y_ast = y_max + 0.05 * abs(y_max);
            for s = 1:numUmani
                if p_1vs1(s) > 0.05
                    %text(s, y_ast, 'MATCH', 'Color', [0.2 0.7 0.2], 'FontSize', 11, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
                end
            end
            
            title(sprintf('%s\n(Umani Eterogenei | Confronti 1-vs-1)', condCorrente), 'FontSize', 12);
        end
        
        ylabel(nomeMetricaPulito, 'FontSize', 11);
        hold off;
    end % Fine ciclo condizioni
    
    if all(isgraphics(h_ax))
        linkaxes(h_ax, 'y'); 
    end
    
end
fprintf('\n>>> Generazione Figure Completata!\n');