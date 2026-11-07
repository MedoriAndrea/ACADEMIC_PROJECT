clear all
close all
clc
% chiamata interfaccia GUI 

global b;
global r;  
global d;
global dist; 

GUI_interface_Speed  % se scriviamo una nuova Gui cambiamo il nome; 
% INTERFACCIA_GUI_Gruppo1

% aspetta che b venga creato
while isempty(evalin('base', 'who(''b'')'))
    pause(0.5);
end
b = evalin('base', 'b');

dist = 0.1025;
d = 0.105; % distanza ruote 
r = 0.035; % raggio

% Trajectory planning with polynomials - iniziaizzazione delle coordinare 
x_i = 0;
y_i = 1;
theta_i = 0;

xf = 3.5; 
yf = 0.4;

% inizializzazione tempo di campionamento 
dt = 0.06;

%% Localization based on EKF
n1=3;
nLandmark=1;
n2=1*nLandmark; % numero di variabili che servono per descrivere la posizione dei landmark

P = eye(n1); % initial state covraiance - identity matrix

X = [x_i;y_i;theta_i]; % salvare posa stimata per istante di tempo 


% creazione della mappa 
Coord_LM_kalman = {[0.3 0.6; 0.5 0.6; 0.5 0.8; 0.3 0.8],[3.1 0.6; 3.3 0.6; 3.3 0.8; 3.1 0.8]}; 
yp = 1.4; % coordinata parete

figure; clf;
hold on;
axis equal;
grid on;

for i = 1:length(Coord_LM_kalman)
    rett = Coord_LM_kalman{i};  % matrice 4x2 dei vertici
    rett = [rett; rett(1,:)];  % chiudi il rettangolo tornando al primo punto
    plot(rett(:,1), rett(:,2), 'b-', 'LineWidth', 2);  % disegna il rettangolo
end

xlim([-1, 4.5]); ylim([-1,4.5]);  % Adatta ai limiti della tua simulazione
grid on;
hold on 
plot( [-0.2, 3.8],[yp,yp], 'b-', 'LineWidth', 2); 
 
xlabel('X [m]');
ylabel('Y [m]');

hold on
plot(x_i, y_i, '*r', 'MarkerSize',9)    % punto iniziale in rosso
plot(xf, yf, '*g', 'MarkerSize',9)      % punto finale in verde

i = 1; 
dati_salvati_kalman = [];
dati_salvati_b_kalman = [];

while true 
        ack = read(b, 1, 'uint8');  % Legge il byte di controllo
        if ack == 1  % Controlla se il byte di controllo è corretto
            encoder = read(b,6,"uint8"); 
            msb_dx = int16(encoder(1)); %trasformazione da decimale a 8 bit
            lsb_dx = int16(encoder(2));
            msb_sx = int16(encoder(3));
            lsb_sx = int16(encoder(4));
            msb_lidar = int16(encoder(5));
            lsb_lidar = int16(encoder(6));

            msbdx_shift = bitshift(msb_dx,8);
            msbsx_shift = bitshift(msb_sx,8);
            msb_lidar_shift = bitshift(msb_lidar,8);
        
            encoderdx_b = double(msbdx_shift+lsb_dx);
            encodersx_b = double(msbsx_shift+lsb_sx);
            lidar_b = double(msb_lidar_shift+lsb_lidar);
            
            dati_salvati_b_kalman = [dati_salvati_b_kalman; encoderdx_b, encodersx_b, lidar_b];
           
            % conversione da bit a radianti 
            encodersx(i) = -(encodersx_b * 2 * pi/4096);
            encoderdx(i) = (-encoderdx_b * 2 * pi/4096);

            % conversione lidar da bit a m: 
            k1 = 37.20; 
            k2 = -0.86;
            adc_max = 2^10 - 1; % risoluzione a 16 bit = 65535
            V_ref = 5.0; % tensione di riferimento (verifica se 5V o 3.3V)
            risoluzione = V_ref / adc_max;
            tensione = lidar_b * risoluzione; %trasforma ADC in tensione elettrica reale
            lidar(i) = (tensione / k1)^(1/k2);   % trasdormazione da tensione a distanza
            lidar(i) = lidar(i) / 100; %[m]

            dati_salvati_kalman = [dati_salvati_kalman; encoderdx(i), encodersx(i), lidar(i)];

            if i > 1
                delta_sx = encodersx(i) - encodersx(i-1); % diff calcola la differenza fra due elementi adiacenti 
                delta_dx = encoderdx(i) - encoderdx(i-1);
                
                if delta_sx > pi
                    delta_sx = delta_sx - 2*pi; 
                elseif delta_sx < -pi
                    delta_sx = delta_sx + 2*pi; 
                end 
                if delta_dx > pi 
                    delta_dx = delta_dx - 2*pi;
                elseif delta_dx < -pi
                    delta_dx = delta_dx + 2*pi;
                end 
               
                % % calcolo la variazione della velocità angolare destra e sinistra
                w_sx = delta_sx/dt;
                w_dx = delta_dx/dt;
                
                % % ricostruisco la velocità lineare e angolare eseguita dalla piattaforma -
                v = r/2 * (w_sx + w_dx); 
                w = r/d * (w_dx - w_sx);
   
                % implementazione filtro di kalman esteso
                Z = lidar (i);
                [X, P] = ekf_2605(n1, n2, yp, X, P, Z, dt, v, w);
                
                hold on;
                plot(X(1), X(2), '*g');
                drawnow
            end 

            i = i+1; 
            drawnow

        end 
        
        drawnow
end 


