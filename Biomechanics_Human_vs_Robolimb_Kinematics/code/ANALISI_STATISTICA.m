% =========================================================================
% ANALISI STATISTICA: Test Normalità, Pooling, Confronto e Trend Trial-by-Trial
% =========================================================================
clc; clear; close all;

fprintf('Caricamento Tabella Statistica Pulita...\n');
if ~exist('TabellaStatistica_Pulita.mat', 'file')
    error('File TabellaStatistica_Pulita.mat non trovato. Esegui prima lo script di pulizia.');
end
load('TabellaStatistica_Pulita.mat', 'TabellaStatistica_Pulita');

% Usiamo una variabile interna con il vecchio nome per non stravolgere il tuo codice
TabellaStatistica = TabellaStatistica_Pulita; 

% 1. IDENTIFICAZIONE AUTOMATICA DELLE METRICHE
colonne_escluse = {'Soggetto', 'Condizione', 'Trial', 'Gruppo', 'Nome_Video', 'Trial_ID'};
metriche = setdiff(TabellaStatistica.Properties.VariableNames, colonne_escluse, 'stable');

condizioni = unique(TabellaStatistica.Condizione);

for c = 1:length(condizioni)
    condCorrente = condizioni(c);
    fprintf('\n======================================================\n');
    fprintf('>>> CONDIZIONE SPERIMENTALE: %s\n', char(condCorrente));
    fprintf('======================================================\n');
    
    datiCond = TabellaStatistica(TabellaStatistica.Condizione == condCorrente, :);
    
    idxHuman = datiCond.Gruppo == 'Human';
    idxRobot = datiCond.Gruppo == 'Robot';
    
    for m = 1:length(metriche)
        metrica = metriche{m};
        
        nomeMetricaPulito = strrep(metrica, '_', ' ');
        fprintf('\n--- Metrica: %s ---\n', nomeMetricaPulito);
        
        % Estrazione grezza
        rawH = datiCond.(metrica)(idxHuman);
        rawR = datiCond.(metrica)(idxRobot);
        soggettiHumanRaw = datiCond.Soggetto(idxHuman);
        
        % Conversione di sicurezza per evitare errori isnan e strcmp
        if iscell(rawH)
            try rawH = cell2mat(rawH); catch, continue; end
        end
        if iscell(rawR)
            try rawR = cell2mat(rawR); catch, continue; end
        end
        
        if ~isnumeric(rawH) || ~isnumeric(rawR)
            continue;
        end
        
        % Forziamo i soggetti a cell array di stringhe per usare strcmp senza errori
        if iscategorical(soggettiHumanRaw)
            soggettiHuman = cellstr(soggettiHumanRaw);
        else
            soggettiHuman = soggettiHumanRaw;
        end
        
        % Pulizia NaN
        validH = ~isnan(rawH);
        validR = ~isnan(rawR);
        valHuman = rawH(validH);
        soggettiHuman = soggettiHuman(validH);
        valRobot = rawR(validR);
        
        if isempty(valHuman) || isempty(valRobot)
            fprintf('Dati insufficienti per il confronto.\n'); 
            continue;
        end
        
        % -----------------------------------------------------------------
        % 1. TEST DI NORMALITÀ (Anderson-Darling integrato)
        % -----------------------------------------------------------------
        [h_norm, p_norm] = swtest(valHuman);
        if h_norm == 0
            fprintf('  [Normalità Umani] Distribuzione Normale (p = %.3f).\n', p_norm);
        else
            fprintf('  [Normalità Umani] NON Normale (p = %.3f).\n', p_norm);
        end
        
        % -----------------------------------------------------------------
        % 2 & 3. OMOGENEITÀ E CONFRONTI (Kruskal-Wallis e Mann-Whitney)
        % -----------------------------------------------------------------
        nomiUmani = unique(soggettiHuman);
        numUmani = length(nomiUmani);
        p_1vs1 = NaN(numUmani, 1); 
        
        if numUmani > 1
            p_kw = kruskalwallis(valHuman, soggettiHuman, 'off');
            fprintf('  [Pooling Umani] Kruskal-Wallis p = %.3f ', p_kw);
            
            if p_kw > 0.05
                fprintf('(Omogenei: Raggruppamento giustificato).\n');
                p_mw_global = ranksum(valHuman, valRobot);
                fprintf('  -> [Human Globale vs Robot] Mann-Whitney p = %.4f\n', p_mw_global);
                p_mw_plot = p_mw_global; 
            else
                fprintf('(ATTENZIONE: Variabilità tra i soggetti).\n');
                fprintf('  -> Eseguo confronti 1-vs-1:\n');
                for s = 1:numUmani
                    val_sog = valHuman(strcmp(soggettiHuman, nomiUmani{s}));
                    if ~isempty(val_sog)
                        p_1vs1(s) = ranksum(val_sog, valRobot);
                        if p_1vs1(s) > 0.05
                            fprintf('     [Umano %s vs Robot] p = %.4f ---> ASSOMIGLIA\n', char(nomiUmani{s}), p_1vs1(s));
                        else
                            fprintf('     [Umano %s vs Robot] p = %.4f ---> DIVERSO\n', char(nomiUmani{s}), p_1vs1(s));
                        end
                    end
                end
                p_mw_plot = NaN; 
            end
        else
            p_mw_plot = ranksum(valHuman, valRobot);
            fprintf('  [Singolo Umano vs Robot] Mann-Whitney p = %.4f\n', p_mw_plot);
        end
        
        % -----------------------------------------------------------------
        % 4. VISUALIZZAZIONE
        % -----------------------------------------------------------------
        figName = sprintf('%s - %s', char(condCorrente), nomeMetricaPulito);
        figure('Name', figName, 'Color', 'w', 'Position', [100, 100, 1100, 500]);
        sgtitle(sprintf('%s - %s', char(condCorrente), nomeMetricaPulito), 'FontSize', 16, 'FontWeight', 'bold');
        
        coloriUmani = lines(numUmani); 
        handlesLegenda = [];
        nomiLegenda = {};
        
        % ====== SUBPLOT 1: BOXPLOT (BIVIO LOGICO) ======
        ax1 = subplot(1, 2, 1);
        pos1 = get(ax1, 'Position'); pos1(4) = 0.75; set(ax1, 'Position', pos1);
        
        if ~isnan(p_mw_plot)
            % --- CASO A: UMANI OMOGENEI (Plot Classico 2 Box) ---
            % Creiamo un array categorico temporaneo per il plot globale
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
            
            title({' ', sprintf('Distribuzione (p-value = %.4f)', p_mw_plot)}, 'FontSize', 12);
            set(gca, 'XTickLabel', {'Human', 'Robolimb'});
            
            if p_mw_plot < 0.05
                y_max = max([valHuman; valRobot]);
                y_ast = y_max + 0.05 * abs(y_max);
                plot([1 2], [y_ast y_ast], '-k', 'LineWidth', 1.5);
                text(1.5, y_ast + 0.02 * abs(y_max), '*', 'FontSize', 22, 'HorizontalAlignment', 'center');
            end
            
        else
            % --- CASO B: UMANI ETEROGENEI (Plot Esploso Multi-Box) ---
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
            
            y_max = max(X_all);
            y_ast = y_max + 0.05 * abs(y_max);
            for s = 1:numUmani
                if p_1vs1(s) > 0.05
                    text(s, y_ast, 'MATCH', 'Color', [0.2 0.7 0.2], 'FontSize', 11, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');
                end
            end
            
            title({' ', 'Confronti Singoli: Kruskal-Wallis p < 0.05'}, 'FontSize', 12);
        end
        
        ylabel(nomeMetricaPulito, 'FontSize', 11);
        hold off;
        
        % ====== SUBPLOT 2: ANDAMENTO TRIAL-BY-TRIAL ======
        ax2 = subplot(1, 2, 2);
        pos2 = get(ax2, 'Position'); pos2(4) = 0.75; set(ax2, 'Position', pos2);
        hold on; grid on;
        
        for s = 1:numUmani
            idx_sog = strcmp(soggettiHuman, nomiUmani{s});
            val_sog = valHuman(idx_sog);
            h_line = plot(1:length(val_sog), val_sog, '-o', 'Color', coloriUmani(s,:), 'LineWidth', 1.5, 'MarkerSize', 6, 'MarkerFaceColor', 'w');
            handlesLegenda(end+1) = h_line;
            nomiLegenda{end+1} = sprintf('Umano: %s', char(nomiUmani{s}));
        end
        
        h_line_rob = plot(1:length(valRobot), valRobot, '-s', 'Color', [0.85 0.1 0.1], 'LineWidth', 2.5, 'MarkerSize', 7, 'MarkerFaceColor', [0.85 0.1 0.1]);
        handlesLegenda(end+1) = h_line_rob;
        nomiLegenda{end+1} = 'Robolimb';
        
        title({' ', 'Andamento Trial-by-Trial'}, 'FontSize', 12);
        xlabel('Numero Trial', 'FontSize', 11);
        ylabel(nomeMetricaPulito, 'FontSize', 11);
        legend(handlesLegenda, nomiLegenda, 'Location', 'best', 'FontSize', 10);
        hold off;
        
    end
end
fprintf('\n>>> Analisi completata!\n');


Tabella_Bidigitale = TabellaStatistica_Pulita(TabellaStatistica_Pulita.Condizione == 'BIDIGITALE', :);

% Prende tutte le righe in cui Condizione è uguale a 'LIBERA' (e tutte le colonne ':')
Tabella_Libera = TabellaStatistica_Pulita(TabellaStatistica_Pulita.Condizione == 'LIBERA', :);