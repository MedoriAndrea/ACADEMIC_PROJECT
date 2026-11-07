% =========================================================================
% SCRIPT DI PRE-PROCESSING BIOMECCANICO 
% (Dati Non Normalizzati, L_indice, e Velocità in cm/s)
% =========================================================================

clc; clear; close all;

% --- PARAMETRI DI CALIBRAZIONE TELECAMERA ---
fx = 624.092189836733; fy = 615.6873830398465;
cx = 328.24299039763036; cy = 231.37862204032436;
Zc = 20.0; % Profondità in cm

basePath = 'data'; 
categorie = {'Human', 'Robot'};
datasetElaborato = struct();

fprintf('=== INIZIO PRE-PROCESSING DATASET ===\n\n');

for c = 1:length(categorie)
    catName = categorie{c};
    catPath = fullfile(basePath, catName);
    if ~exist(catPath, 'dir'), continue; end
    
    fprintf('Elaborazione Categoria: %s...\n', catName);
    soggetti = dir(catPath);
    soggetti = soggetti([soggetti.isdir] & ~startsWith({soggetti.name}, '.'));
    
    for s = 1:length(soggetti)
        sogName = soggetti(s).name;
        sogPath = fullfile(catPath, sogName);
        
        nomiParti = strsplit(sogName, '_');
        if length(nomiParti) >= 2
            idSoggetto = nomiParti{1}; condizione = nomiParti{2};
        else
            idSoggetto = sogName; condizione = 'UNKNOWN';
        end
        
        validCond = matlab.lang.makeValidName(upper(condizione));
        validSog  = matlab.lang.makeValidName(idSoggetto);
        fprintf('  -> Condizione: %s | Soggetto: %s...\n', validCond, validSog);
        
        trials = dir(sogPath);
        trials = trials([trials.isdir] & ~startsWith({trials.name}, '.'));
        
        for t = 1:length(trials)
            trialName = trials(t).name;
            trialPath = fullfile(sogPath, trialName);
            
            fileAngoli = fullfile(trialPath, 'angles.csv');
            fileMarker = fullfile(trialPath, 'markers_px.csv');
            
            if exist(fileAngoli, 'file') && exist(fileMarker, 'file')
                
                % --- STEP 1: ESTRAZIONE ANGOLI E LUNGHEZZA INDICE ---
                tabAngoli = readtable(fileAngoli);
                mcpAngles = tabAngoli.MCP_deg;
                pipAngles = tabAngoli.PIP_deg; % Estrazione angolo PIP
                timeSteps = tabAngoli.time_s;
                numFrames = height(tabAngoli);
                
                % Estrazione lunghezza dito (solo prima riga)
                L_mcp_pip = tabAngoli.L_mcp_pip_cm(1);
                L_pip_dip = tabAngoli.L_pip_dip_cm(1);
                L_dip_tip = tabAngoli.L_dip_tip_cm(1);
                L_indice_tot = L_mcp_pip + L_pip_dip + L_dip_tip;
                
                % --- STEP 2: CONVERSIONE E CAMBIO COORDINATE ---
                tabMarker = readtable(fileMarker);
                
                % Vettori per Posizioni e Velocità Locali
                tipLocalX = zeros(numFrames, 1);
                tipLocalY = zeros(numFrames, 1);
                tipLocalVx = zeros(numFrames, 1);
                tipLocalVy = zeros(numFrames, 1);
                tipVtot = zeros(numFrames, 1);
                
                listaFrames = unique(tabMarker.frame);
                for fIdx = 1:length(listaFrames)
                    currentFrame = listaFrames(fIdx);
                    subTab = tabMarker(tabMarker.frame == currentFrame, :);
                    
                    % Lettura posizioni in pixel
                    palm_px = [subTab.x_filt_px(strcmp(subTab.marker, 'b')), subTab.y_filt_px(strcmp(subTab.marker, 'b'))];
                    mcp_px  = [subTab.x_filt_px(strcmp(subTab.marker, 'm')), subTab.y_filt_px(strcmp(subTab.marker, 'm'))];
                    tip_px  = [subTab.x_filt_px(strcmp(subTab.marker, 't')), subTab.y_filt_px(strcmp(subTab.marker, 't'))];
                    
                    % Lettura velocità in pixel/s
                    tip_vx_px = subTab.vx_px_s(strcmp(subTab.marker, 't'));
                    tip_vy_px = subTab.vy_px_s(strcmp(subTab.marker, 't'));
                    
                    if isempty(palm_px) || isempty(mcp_px) || isempty(tip_px) || isempty(tip_vx_px)
                        continue; 
                    end
                    
                    % Conversione Posizione in cm
                    p_palm = [(palm_px(1) - cx)/fx * Zc, (palm_px(2) - cy)/fy * Zc];
                    p_mcp  = [(mcp_px(1) - cx)/fx * Zc,  (mcp_px(2) - cy)/fy * Zc];
                    p_tip  = [(tip_px(1) - cx)/fx * Zc,  (tip_px(2) - cy)/fy * Zc];
                    
                    % Conversione Velocità in cm/s (Nessuna sottrazione del centro ottico)
                    v_tip_cm = [tip_vx_px * (Zc / fx), tip_vy_px * (Zc / fy)];
                    
                    % Sistema locale su MCP
                    Vx = p_mcp - p_palm;
                    ux = Vx / norm(Vx);
                    uy = [-ux(2), ux(1)];
                    
                    % Proiezione Posizione Relativa
                    p_tip_rel = p_tip - p_mcp;
                    tipLocalX(fIdx) = dot(p_tip_rel, ux);
                    tipLocalY(fIdx) = dot(p_tip_rel, uy);
                    
                    % Proiezione Velocità
                    tipLocalVx(fIdx) = dot(v_tip_cm, ux);
                    tipLocalVy(fIdx) = dot(v_tip_cm, uy);
                    tipVtot(fIdx) = norm(v_tip_cm); % Il modulo non cambia ruotando gli assi
                end
                
                % --- STEP 3: SALVATAGGIO NEL DATASET ---
                datasetElaborato.(catName).(validCond).(validSog).(trialName).Time = timeSteps;
                datasetElaborato.(catName).(validCond).(validSog).(trialName).MCP_Angle = mcpAngles;
                datasetElaborato.(catName).(validCond).(validSog).(trialName).PIP_Angle = pipAngles;
                datasetElaborato.(catName).(validCond).(validSog).(trialName).L_indice = L_indice_tot;
                
                % Coordinate Reali (cm)
                datasetElaborato.(catName).(validCond).(validSog).(trialName).TIP_Local_X = tipLocalX;
                datasetElaborato.(catName).(validCond).(validSog).(trialName).TIP_Local_Y = tipLocalY;
                
                % Velocità (cm/s)
                datasetElaborato.(catName).(validCond).(validSog).(trialName).TIP_Local_Vx = tipLocalVx;
                datasetElaborato.(catName).(validCond).(validSog).(trialName).TIP_Local_Vy = tipLocalVy;
                datasetElaborato.(catName).(validCond).(validSog).(trialName).TIP_Vtot = tipVtot;
            end
        end
    end
end

save('dataset_biomeccanico_elaborato.mat', 'datasetElaborato');
fprintf('=== PRE-PROCESSING TERMINATO CON SUCCESSO ===\n');