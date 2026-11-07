time  = acc_x.time;

label = "passo2";
patient = "paziente9";

N = length(acc_y.signals.values);
matrice = zeros(N,2);

for i = 1:N
    matrice(i,1) = acc_x.signals.values(i);
    matrice(i,2) = acc_y.signals.values(i);
    matrice(i,3) = acc_z.signals.values(i);
    matrice(i,4) = gyr_x.signals.values(i);
    matrice(i,5) = gyr_y.signals.values(i);
    matrice(i,6) = gyr_z.signals.values(i);

end

% Se il dataset non esiste ancora, lo creo
if ~exist('dataset','var')
    dataset = struct('time', {}, 'label', {}, 'matrix', {}, 'patient', {});
end

% --- Se esiste un file dataset.mat, lo carico ---
if isfile('dataset.mat')
    load('dataset.mat','dataset');
end


% Indice della nuova riga (run)
k = numel(dataset) + 1;

% Aggiungo la nuova riga
dataset(k).time   = time;    % 101x1 double
dataset(k).label  = label;   % stringa
dataset(k).matrix = matrice; % 101x6 double
dataset(k).patient  = patient;   % stringa

disp("Nuova riga aggiunta: dataset(" + k + ")");

save('dataset.mat','dataset');   % Salva veramente il dataset su disco





