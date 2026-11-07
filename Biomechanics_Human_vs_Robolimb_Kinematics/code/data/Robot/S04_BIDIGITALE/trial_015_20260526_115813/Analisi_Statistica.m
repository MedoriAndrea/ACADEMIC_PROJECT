% =========================================================================
% ANALISI CINEMATICA WITHIN-HAND (SISTEMA LOCALE NORMALIZZATO)
% =========================================================================

% 1. Caricamento dei dati dai file CSV
T_markers = readtable('markers_px.csv');
T_tip = readtable('tip_kinematics.csv');

% 2. Inizializzazione dei vettori dei risultati
N = height(T_tip);
x_norm = NaN(N, 1); % Inizializzo con Not-a-Number per gestire eventuali marker persi
y_norm = NaN(N, 1);

for k = 1:N
    current_frame = T_tip.frame(k);
    
    % Estraggo le coordinate del TIP in pixel per il frame corrente
    x_tip = T_tip.x_px(k);
    y_tip = T_tip.y_px(k);
    
    % Filtro la tabella dei markers prendendo solo le 5 righe di QUESTO frame
    idx_frame = T_markers.frame == current_frame;
    T_current = T_markers(idx_frame, :);
    
    % Trovo la riga esatta del Palmo ('b') e del MCP ('m')
    idx_palm = strcmp(T_current.marker, 'b');
    idx_mcp  = strcmp(T_current.marker, 'm');
    
    % Controllo di sicurezza: se in questo frame la telecamera non ha 
    % visto il palmo o l'mcp, salto il calcolo (rimarrà un NaN)
    if sum(idx_palm) == 0 || sum(idx_mcp) == 0
        continue;
    end
    
    % Estraggo le X e Y filtrate
    X_palm = T_current.x_filt_px(idx_palm);
    Y_palm = T_current.y_filt_px(idx_palm);
    X_mcp  = T_current.x_filt_px(idx_mcp);
    Y_mcp  = T_current.y_filt_px(idx_mcp);
    
    % --- MATEMATICA DEL SISTEMA DI RIFERIMENTO LOCALE ---
    
    % 1. Creo il Vettore che unisce Palmo e MCP
    v_x = [X_mcp - X_palm, Y_mcp - Y_palm];
    
    % 2. Calcolo la lunghezza del segmento (il nostro "righello" per normalizzare)
    L_metacarpo = norm(v_x);
    
    % 3. Versore dell'Asse X (vettore di lunghezza 1 che punta verso l'MCP)
    i_hat = v_x / L_metacarpo;
    
    % 4. Versore dell'Asse Y (vettore perpendicolare ruotato di 90 gradi)
    j_hat = [-i_hat(2), i_hat(1)];
    
    % 5. Creo il Vettore che va dalla nuova Origine (Palmo) al TIP
    v_tip = [x_tip - X_palm, y_tip - Y_palm];
    
    % 6. Proietto il vettore del TIP sui nuovi assi (tramite Prodotto Scalare)
    x_local = dot(v_tip, i_hat);
    y_local = dot(v_tip, j_hat);
    
    % --- NORMALIZZAZIONE ---
    % Divido le coordinate locali per la lunghezza del metacarpo
    x_norm(k) = x_local / L_metacarpo;
    y_norm(k) = y_local / L_metacarpo;
end

% =========================================================================
% 3. PLOT DELLA TRAIETTORIA
% =========================================================================

figure('Color', 'w', 'Name', 'Within-Hand Kinematics');
% Disegno la traiettoria blu
plot(x_norm, y_norm, '-o', 'LineWidth', 1.5, 'MarkerSize', 3, 'Color', [0 0.4470 0.7410]);
hold on;

% Segno la nuova Origine (Il Palmo) con una Stella Rossa
plot(0, 0, 'p', 'MarkerSize', 18, 'MarkerEdgeColor', 'red', 'MarkerFaceColor', 'red');

% Segno l'articolazione MCP (Sarà FISSA a coordinate 1,0 per chiunque!)
plot(1, 0, 's', 'MarkerSize', 12, 'MarkerEdgeColor', 'black', 'MarkerFaceColor', 'black');

% Disegno l'asse X (il Metacarpo)
line([0 1], [0 0], 'Color', 'k', 'LineWidth', 2, 'LineStyle', '--');

% Impostazioni grafiche
axis equal; % FONDAMENTALE: non deforma le proporzioni spaziali
grid on;
title('Traiettoria Within-Hand Normalizzata del TIP', 'FontSize', 14);
xlabel('Asse X (Distanza Normalizzata Palmo \rightarrow MCP)', 'FontSize', 12);
ylabel('Asse Y (Flessione perpendicolare)', 'FontSize', 12);
legend('Traiettoria Dito Indice (TIP)', 'Palmo (Origine 0,0)', 'Articolazione MCP (Fissa 1,0)', 'Asse del Metacarpo', 'Location', 'best');