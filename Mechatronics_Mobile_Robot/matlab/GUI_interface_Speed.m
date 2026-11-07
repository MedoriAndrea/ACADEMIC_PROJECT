function varargout = GUI_interface_Speed(varargin)
% GUI_INTERFACE_SPEED MATLAB code for GUI_interface_Speed.fig
%      GUI_INTERFACE_SPEED, by itself, creates a new GUI_INTERFACE_SPEED or raises the existing
%      singleton*.
%
%      H = GUI_INTERFACE_SPEED returns the handle to a new GUI_INTERFACE_SPEED or the handle to
%      the existing singleton*.
%
%      GUI_INTERFACE_SPEED('CALLBACK',hObject,eventData,handles,...) calls the local
%      function named CALLBACK in GUI_INTERFACE_SPEED.M with the given input arguments.
%
%      GUI_INTERFACE_SPEED('Property','Value',...) creates a new GUI_INTERFACE_SPEED or raises the
%      existing singleton*.  Starting from the left, property value pairs are
%      applied to the GUI before GUI_interface_Speed_OpeningFcn gets called.  An
%      unrecognized property name or invalid value makes property application
%      stop.  All inputs are passed to GUI_interface_Speed_OpeningFcn via varargin.
%
%      *See GUI Options on GUIDE's Tools menu.  Choose "GUI allows only one
%      instance to run (singleton)".
%
% See also: GUIDE, GUIDATA, GUIHANDLES

% Edit the above text to modify the response to help GUI_interface_Speed

% Last Modified by GUIDE v2.5 17-May-2025 23:11:52

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @GUI_interface_Speed_OpeningFcn, ...
                   'gui_OutputFcn',  @GUI_interface_Speed_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


% --- Executes just before GUI_interface_Speed is made visible.
function GUI_interface_Speed_OpeningFcn(hObject, eventdata, handles, varargin)
% This function has no output args, see OutputFcn.
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
% varargin   command line arguments to GUI_interface_Speed (see VARARGIN)

% Choose default command line output for GUI_interface_Speed
handles.output = hObject;

% Update handles structure
guidata(hObject, handles);

% UIWAIT makes GUI_interface_Speed wait for user response (see UIRESUME)
% uiwait(handles.figure1);


% --- Outputs from this function are returned to the command line.
function varargout = GUI_interface_Speed_OutputFcn(hObject, eventdata, handles) 
% varargout  cell array for returning output args (see VARARGOUT);
% hObject    handle to figure
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% Get default command line output from handles structure
varargout{1} = handles.output;


% --- Executes on button press in Connessione.
function Connessione_Callback(hObject, eventdata, handles)
% hObject    handle to Connessione (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with hcandles and user data (see GUIDATA)
global b;
%b = serialport("COM9", 57600);  % Sostituisci "COMx" 
b=bluetooth("LAZZARO"); %EFFETTUO CONNESSIONE TRA PC E BT
display('connected');  % appare 'connected'
handles.b=b;           % si crea la variabile b nel workspace
assignin('base','b',b) %parametro da aggiungere nella struttura globale dell'interfaccia perche serve anche nelle altre funzioni
                                    %nelle funzioni dei led questo invece
                                    %non lo fai 


% Definizioni parametri 
r = 0.035;
d = 0.105;
handles.r = r;
handles.d = d;
vc = r*5.23; % velocità lineare di comando massima possibile con i nostri parametri; calcolata manualmente (5.23 rad/s è la velocità massima ammissibile della ruota DX e SX)
wc = r*((2*5.23)/d); % velocità angolare di comando massima (stesso ragionamento di vc)
handles.vc = vc;
handles.wc = wc;
dv = 0.1;
dw = 0.05;
%parametri per + e -
% inizializzazione di v e w corrente
handles.v = handles.vc/2; % parametri fissi: non verranno più toccati handles.vc e handles.wc perchè in ogni comando, apparte + e -, vengono ridefiniti
handles.w = handles.wc/2; % invece handles.v e handles.w rappresentano le velocità correnti che, dopo questa prima lettura, con cui parte la macchina, vengono di volta in volta aggiornate in + e -, infatti si trovano SOLO Lì
handles.dv = dv; % passo di aumento/diminuzione velocità lineare per + e -
handles.dw = dw; % passo di aumento/diminuzione velocità angolare per + e -
guidata(hObject, handles);


% --- Executes on button press in Avanti_Sinistra.
function Avanti_Sinistra_Callback(hObject, eventdata, handles)
% hObject    handle to Avanti_Sinistra (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
b = handles.b;
r = handles.r;
d = handles.d;
wc = handles.wc; % essendo ridefinite, wc e vc non cambieranno mai
vc = handles.vc;

% calcoli specifici per il comando
w = wc/2; % come velocità corrente diamo la metà della velocità angolare di comando massima 
v = vc/2; % stessa cosa per la velocità lineare

%omR = (2*v + w*d)/(2*r); % estratte manualmente dal sistema
%omL = (2*v - w*d)/(2*r); % poichè la velocità angolare di comando massima che possiamo dare è inferiore alla velocità massima ammissibile delle ruote DX e SX
% non c'è rischio che possano superare quelle ammissibili
omL =1.5;
omR = 2.615;
% mappatura rad/s -> µs
tR  = uint16( round(1500 - 200* omR/5.23) ); 
tL  = uint16( round(1500 + 200* omL/5.23) );
% pacchetto [01 tL tR]
tR_msb = bitshift(tR, -8);
tR_lsb = bitand(tR, 255);
tL_msb = bitshift(tL, -8);
tL_lsb = bitand(tL, 255);
ack = 1;
write(handles.b, [ack, tR_msb, tR_lsb, tL_msb,tL_lsb], "uint8"); % unico write per inviare i comandi al modulo BT (possiamo anche mettere due 'write')
display('tR,tL');
display(tR);
display(tL);
handles.v = v;      %  <-- le due righe famose
handles.w = w;
guidata(hObject, handles);

% --- Executes on button press in Sinistra.
function Sinistra_Callback(hObject, eventdata, handles)
% hObject    handle to Sinistra (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
b = handles.b;
r = handles.r;
d = handles.d;
wc = handles.wc;
vc = handles.vc;
guidata(hObject, handles);

% calcoli specifici per il comando
w = wc/2;
v = 0;

%omR = (2*v + w*d)/(2*r);
%omL = (2*v - w*d)/(2*r);
omL = 0.524;
omR = 1.5;
% mappatura rad/s -> µs
tR  = uint16( round(1500 - 200* omR/5.23) );
tL  = uint16( round(1500 + 200* omL/5.23) );
% pacchetto [01 tL tR]
tR_msb = bitshift(tR, -8);
tR_lsb = bitand(tR, 255);
tL_msb = bitshift(tL, -8);
tL_lsb = bitand(tL, 255);
ack = 1;
write(handles.b, [ack, tR_msb, tR_lsb, tL_msb,tL_lsb], "uint8"); % per inviare i comandi al modulo BT
display('tR,tL');
display(tR);
display(tL);


% --- Executes on button press in Avanti.
function Avanti_Callback(hObject, eventdata, handles)
% hObject    handle to Avanti (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
b = handles.b;
r = handles.r;
d = handles.d;
wc = handles.wc;
vc = handles.vc;


% calcoli specifici per il comando
w = 0;
v = vc;

%omR = (2*v + w*d)/(2*r);
%mL = (2*v - w*d)/(2*r);
omR = 2.62;
omL = 2.62;

% mappatura rad/s -> µs
tR  = uint16( round(1500 - 200* omR/5.23) );
tL  = uint16( round(1500 + 200* omL/5.23) );
% pacchetto [01 tL tR]
tR_msb = bitshift(tR, -8);
tR_lsb = bitand(tR, 255);
tL_msb = bitshift(tL, -8);
tL_lsb = bitand(tL, 255);
ack = 1;
write(handles.b, [ack, tR_msb, tR_lsb, tL_msb,tL_lsb], "uint8"); % per inviare i comandi al modulo BT
display('tR,tL');
display(tR);
display(tL);
   
handles.v = v;      %  <-- le due righe famose
handles.w = w;
guidata(hObject, handles);

% --- Executes on button press in Stop.
function Stop_Callback(hObject, eventdata, handles)
% hObject    handle to Stop (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
b = handles.b;
r = handles.r;
d = handles.d;
wc = handles.wc;
vc = handles.vc;
guidata(hObject, handles);

% calcoli specifici per il comando
w = 0;
v = 0;

omR = (2*v + w*d)/(2*r);
omL = (2*v - w*d)/(2*r);

% mappatura rad/s -> µs
tR  = uint16( round(1500 - 200* omR/5.23) );
tL  = uint16( round(1500 + 200* omL/5.23) );
% pacchetto [01 tL tR]
tR_msb = bitshift(tR, -8);
tR_lsb = bitand(tR, 255);
tL_msb = bitshift(tL, -8);
tL_lsb = bitand(tL, 255);
ack = 1;
write(handles.b, [ack, tR_msb, tR_lsb, tL_msb,tL_lsb], "uint8"); % per inviare i comandi al modulo BT
display('tR,tL');
display(tR);
display(tL);
   


% --- Executes on button press in Indietro_Sinistra.
function Indietro_Sinistra_Callback(hObject, eventdata, handles)
% hObject    handle to Indietro_Sinistra (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
b = handles.b;
r = handles.r;
d = handles.d;
wc = handles.wc;
vc = handles.vc;


% calcoli specifici per il comando
w = wc/2;
v = -vc/2;

%omR = (2*v + w*d)/(2*r);
omR =  -3.2;
omL = -1.5;
%omL = (2*v - w*d)/(2*r);

% mappatura rad/s -> µs
tR  = uint16( round(1500 - 200* omR/5.23) );
tL  = uint16( round(1500 + 200* omL/5.23) );
% pacchetto [01 tL tR]
tR_msb = bitshift(tR, -8);
tR_lsb = bitand(tR, 255);
tL_msb = bitshift(tL, -8);
tL_lsb = bitand(tL, 255);
ack = 1;
write(handles.b, [ack, tR_msb, tR_lsb, tL_msb,tL_lsb], "uint8"); % per inviare i comandi al modulo BT
display('tR,tL');
display(tR);
display(tL);

handles.v = v;      %  <-- le due righe famose
handles.w = w;
guidata(hObject, handles);

% --- Executes on button press in Indietro.
function Indietro_Callback(hObject, eventdata, handles)
% hObject    handle to Indietro (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
b = handles.b;
r = handles.r;
d = handles.d;
wc = handles.wc;
vc = handles.vc;

% calcoli specifici per il comando
w = 0;
v = -vc/2;

omR = (2*v + w*d)/(2*r);
omL = (2*v - w*d)/(2*r);

% mappatura rad/s -> µs
tR  = uint16( round(1500 - 200* omR/5.23) );
tL  = uint16( round(1500 + 200* omL/5.23) );
% pacchetto [01 tL tR]
tR_msb = bitshift(tR, -8);
tR_lsb = bitand(tR, 255);
tL_msb = bitshift(tL, -8);
tL_lsb = bitand(tL, 255);
ack = 1;
write(handles.b, [ack, tR_msb, tR_lsb, tL_msb,tL_lsb], "uint8"); % per inviare i comandi al modulo BT
display('tR,tL');
display(tR);
display(tL);
   
handles.v = v;      %  <-- le due righe famose
handles.w = w;
guidata(hObject, handles);


% --- Executes on button press in Avanti_destra.
function Avanti_destra_Callback(hObject, eventdata, handles)
% hObject    handle to Avanti_destra (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
b = handles.b;
r = handles.r;
d = handles.d;
wc = handles.wc;
vc = handles.vc;


% calcoli specifici per il comando
w = -wc/2;
v = vc/2;

%omR = (2*v + w*d)/(2*r);
omR = 1.3;
omL = 1.70;
%omL = (2*v - w*d)/(2*r);

% mappatura rad/s -> µs
tR  = uint16( round(1500 - 200* omR/5.23) );
tL  = uint16( round(1500 + 200* omL/5.23) );
% pacchetto [01 tL tR]
tR_msb = bitshift(tR, -8);
tR_lsb = bitand(tR, 255);
tL_msb = bitshift(tL, -8);
tL_lsb = bitand(tL, 255);
ack = 1;
write(handles.b, [ack, tR_msb, tR_lsb, tL_msb,tL_lsb], "uint8"); % per inviare i comandi al modulo BT
display('tR,tL');
display(tR);
display(tL);

handles.v = v;      %  <-- le due righe famose
handles.w = w;
guidata(hObject, handles);


% --- Executes on button press in Destra.
function Destra_Callback(hObject, eventdata, handles)
% hObject    handle to Destra (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
b = handles.b;
r = handles.r;
d = handles.d;
wc = handles.wc;
vc = handles.vc;
guidata(hObject, handles);

% calcoli specifici per il comando
w = -wc/2;
v = 0;

%omR = (2*v + w*d)/(2*r);
%mL = (2*v - w*d)/(2*r);
omR = 0.524;
omL = 1.5;
% mappatura rad/s -> µs
tR  = uint16( round(1500 - 200* omR/5.23) );
tL  = uint16( round(1500 + 200* omL/5.23) );
% pacchetto [01 tL tR]
tR_msb = bitshift(tR, -8);
tR_lsb = bitand(tR, 255);
tL_msb = bitshift(tL, -8);
tL_lsb = bitand(tL, 255);
ack = 1;
write(handles.b, [ack, tR_msb, tR_lsb, tL_msb,tL_lsb], "uint8"); % per inviare i comandi al modulo BT
display('tR,tL');
display(tR);
display(tL);


% --- Executes on button press in Indietro_Destra.
function Indietro_Destra_Callback(hObject, eventdata, handles)
% hObject    handle to Indietro_Destra (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
b = handles.b;
r = handles.r;
d = handles.d;
wc = handles.wc;
vc = handles.vc;


% calcoli specifici per il comando
w = -wc/2;
v = -vc/2;

omR = -5.1;
omL = -4.5;
%omR = (2*v + w*d)/(2*r);
%omL = (2*v - w*d)/(2*r);

% mappatura rad/s -> µs
tR  = uint16( round(1500 - 200* omR/5.23) );
tL  = uint16( round(1500 + 200* omL/5.23) );
% pacchetto [01 tL tR]
tR_msb = bitshift(tR, -8);
tR_lsb = bitand(tR, 255);
tL_msb = bitshift(tL, -8);
tL_lsb = bitand(tL, 255);
ack = 1;
write(handles.b, [ack, tR_msb, tR_lsb, tL_msb,tL_lsb], "uint8"); % per inviare i comandi al modulo BT
display('tR,tL');
display(tR);
display(tL);

handles.v = v;      %  <-- le due righe famose
handles.w = w;
guidata(hObject, handles);


% --- Executes on button press in Aumenta.
function Aumenta_Callback(hObject, eventdata, handles)
% hObject    handle to Aumenta (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
b = handles.b;
r = handles.r;
d = handles.d;

vc = handles.vc;
wc = handles.wc;
v0 = handles.v; % l'ultima velocità letta la salviamo qua, che nel primo caso + quella di inizializzazione, ma poi cambierà
w0 = handles.w;
dv = handles.dv;
dw = handles.dw;

v = min(vc, v0+dv); % controllo che mi permette in ogni caso di prendere la velocità minima tra quella attuale aumentata e quella massima possibile
% mi assicura anche di prendere la velocità attuale e non la massima, ad
% eccezione di quando coincidono
w = w0;

handles.v = v; % le nuove velocità calcolate le salviamo nel nuovo handles.v e handles.w che verrà usato dopo
handles.w = w;

guidata(hObject, handles); % salviamo tutti gli handles attuali

omR = (2*v + w*d)/(2*r);
omL = (2*v - w*d)/(2*r);

% mappatura rad/s -> µs
tR  = uint16( round(1500 - 200* omR/5.23) );
tL  = uint16( round(1500 + 200* omL/5.23) );
% pacchetto [01 tL tR]
tR_msb = bitshift(tR, -8);
tR_lsb = bitand(tR, 255);
tL_msb = bitshift(tL, -8);
tL_lsb = bitand(tL, 255);
ack = 1;
write(handles.b, [ack, tR_msb, tR_lsb, tL_msb,tL_lsb], "uint8"); % per inviare i comandi al modulo BT
display('tR,tL');
display(tR);
display(tL);


% --- Executes on button press in Diminuisci.
function Diminuisci_Callback(hObject, eventdata, handles)
% hObject    handle to Diminuisci (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
b = handles.b;
r = handles.r;
d = handles.d;

vc = handles.vc;
wc = handles.wc;
v0 = handles.v;  % l'ultima velocità letta la salviamo qua 
w0 = handles.w;
dv = handles.dv;
dw = handles.dw;

v = max(-vc, v0-dv); % controllo che mi permette in ogni caso di prendere la velocità massima tra quella attuale diminuita e quella minima possibile
% mi assicura anche di prendere la velocità attuale e non la minima, ad
% eccezione di quando coincidono
w = w0;
%w = max(-wc, w0-dw);

handles.v = v; % le nuove velocità calcolate le salviamo qua
handles.w = w;

guidata(hObject, handles); % salviamo tutti gli handles attuali

omR = (2*v + w*d)/(2*r);
omL = (2*v - w*d)/(2*r);

% mappatura rad/s -> µs
tR  = uint16( round(1500 - 200* omR/5.23) );
tL  = uint16( round(1500 + 200* omL/5.23) );
% pacchetto [01 tL tR]
tR_msb = bitshift(tR, -8);
tR_lsb = bitand(tR, 255);
tL_msb = bitshift(tL, -8);
tL_lsb = bitand(tL, 255);
ack = 1;
write(handles.b, [ack, tR_msb, tR_lsb, tL_msb,tL_lsb], "uint8"); % per inviare i comandi 
display('tR,tL');
display(tR);
display(tL);
