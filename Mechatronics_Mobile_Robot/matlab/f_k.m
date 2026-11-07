%% Funzione integrazione Runge-Kutta di secondo ordine
function output = f_k(x_k, y_k, theta_k, T_s, v, omega)
    output = [ x_k + T_s*v*cos(theta_k + (T_s*omega)/2);
               y_k + T_s*v*sin(theta_k + (T_s*omega)/2);
               theta_k + T_s*omega];
end