function [X,C] = ekf_2605(n1,n2,yp,x,P,Z,dt,v,w)
% X = stima della posa finale corretta, C = matrice di covarianza
% Z = distanza euclidea LiDAR parete-piattaforma

v_ = 0.01;
w_ = 0.05;  % più robusto contro rumore lidar

%w_=0.05; % da aumentare 


V_k = v_^2*eye(n1);
W_k = w_^2*eye(n2);

%% Calcolo dello stato predetto
odometria = f_k(x(1),x(2),x(3),dt,v,w);

F = J1(odometria(1),odometria(2),odometria(3),dt,v,w);

P = F*P*F'+V_k; 

%% Calcolo stato stimato
H = J2(odometria(1),odometria(2),odometria(3),yp);

% Innovazione 
nu = Z - h_k(odometria(1),odometria(2),odometria(3),yp);

% Calcolo della matrice di guadagno del filtro 
R = P*H'/(H*P*H'+ W_k);

nu = reshape(nu, [], 1);
X = odometria + R * nu ;

% Calcolo della matrice di covarianza
C = P - R*H*P;


% disp(['Z = ', num2str(Z), ', h_k = ', num2str(h_k(odometria(1), odometria(2), odometria(3), yp))])

%% functions 
function output = f_k(x_k, y_k, theta_k, T_s, v, omega) % con f_k si intendono le formule di Runge-Kutta

 output = [ x_k + T_s*v*cos(theta_k + (T_s*omega)/2);
            y_k + T_s*v*sin(theta_k + (T_s*omega)/2);
                      theta_k + T_s*omega];
end



function output = J1(x_k, y_k, theta_k, T_s, v, omega)

 output = [ 1, 0, -T_s*v*sin(theta_k + (T_s*omega)/2);
            0, 1,  T_s*v*cos(theta_k + (T_s*omega)/2);
            0, 0,                                   1];
end


function output = h_k(x_k, y_k, theta_k, yp)
    
        output = -(y_k - yp);

end



 function output = J2(x_k, y_k, theta_k, yp)
    
        output = [0, -1, 0];
 end



end

