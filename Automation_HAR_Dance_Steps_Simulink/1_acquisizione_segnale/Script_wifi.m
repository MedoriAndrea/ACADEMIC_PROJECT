%% ================================
%  SCRIPT per connessione ADB Wi-Fi
%  Da eseguire ogni volta che apri MATLAB
%% ================================

% 1. Aggiungo adb.exe al PATH
setenv('PATH', [getenv('PATH') ';C:\Users\Marco\AppData\Local\Android\Sdk\platform-tools']);

% 2. Mostro i device (serve per vedere se è collegato via USB la prima volta)
disp('--- Device ADB attuali ---');
!adb devices

% 3. Passo il telefono in modalità TCP
disp('--- Imposto ADB su TCP port 5555 ---');
!adb tcpip 5555

% 4. Connessione al telefono via Wi-Fi
disp('--- Connessione a 172.20.10.3:5555 ---');
!adb connect 172.20.10.3:5555

% 5. Verifica finale
disp('--- Device ADB dopo connessione Wi-Fi ---');
!adb devices
