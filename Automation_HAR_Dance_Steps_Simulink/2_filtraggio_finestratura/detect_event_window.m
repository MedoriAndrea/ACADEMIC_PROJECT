function ROI = detect_event_window(signal, time)

    % Parametri finestra
    preSamples  = 200;
    postSamples = 570;
    threshold   = 1.7; 

    % Inizializza ROI
    ROI = [];

    idx = 1;
    while idx <= length(signal)
        if signal(idx) > threshold
            % Bordo sinistro
            startIdx = max(idx - preSamples, 1);
            % Bordo destro
            endIdx = min(idx + postSamples, length(signal));

            % Salva finestra
            ROI = [ROI; startIdx, endIdx];

            % Salta oltre la finestra per cercare il prossimo evento
            idx = endIdx + 1;
        else
            
            idx = idx + 1;
        end
    end
end