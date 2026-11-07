#include <16F887.h>
#device ICD=TRUE ADC=10
#fuses HS, NOLVP, NOWDT

#use delay(clock=20000000)
#use rs232(baud=9600, xmit=PIN_A1, rcv=PIN_A3, stream=BT)
#use i2c(MASTER, SDA=PIN_D0, SCL=PIN_C3, FAST, stream=ENCODER_DX)
#use i2c(MASTER, SDA=PIN_D1, SCL=PIN_D2, FAST, stream=ENCODER_SX)

#define AS5600_ADDRESS 0x36
#define AS5600_ANGLE   0x0E
#define Motore_dx PIN_B2
#define Motore_sx PIN_B3


int1 startFlag = 0;
int1 motorFlag = 0;
int1 sensFlag  = 0;


int8 sensCounter = 0;
int8 SENSOR_PERIOD = 3;
int16 THigh_dx = 1500;
int16 THigh_sx = 1500;


#int_timer2
void timer2_isr() {
    startFlag = 1;
}

void invia_dati_sensori() {
    int8 msb_dx, lsb_dx, msb_sx, lsb_sx,msb_lidar,lsb_lidar;
    int16 valore_adc;

    // Encoder DX
    i2c_start(ENCODER_DX);
    i2c_write((AS5600_ADDRESS<<1));
    i2c_write(AS5600_ANGLE);
    i2c_start(ENCODER_DX);
    i2c_write((AS5600_ADDRESS<<1)|1);
    msb_dx = i2c_read(1);
    lsb_dx = i2c_read(0);
    i2c_stop(ENCODER_DX);

    // Encoder SX
    i2c_start(ENCODER_SX);
    i2c_write((AS5600_ADDRESS<<1));
    i2c_write(AS5600_ANGLE);
    i2c_start(ENCODER_SX);
    i2c_write((AS5600_ADDRESS<<1)|1);
    msb_sx = i2c_read(1);
    lsb_sx = i2c_read(0);
    i2c_stop(ENCODER_SX);

    valore_adc = read_adc();
    msb_lidar=make8(valore_adc,1);
    lsb_lidar=make8(valore_adc,0);
    
    putc(1, BT);
    putc(msb_dx, BT);
    putc(lsb_dx, BT);
    putc(msb_sx, BT);
    putc(lsb_sx, BT);

    putc(msb_lidar,BT);
    putc(lsb_lidar,BT);
   
}


void main() {
    

 setup_adc_ports(sAN2);
 setup_adc(ADC_CLOCK_INTERNAL);
 set_adc_channel(2);
 delay_us(10);
   

    
    setup_timer_2(T2_DIV_BY_16, 196, 16);
    enable_interrupts(INT_TIMER2);
    enable_interrupts(GLOBAL);

    while (TRUE) {
        
        if (startFlag) {
            startFlag = 0;
            motorFlag = 1;

            
            if (++sensCounter >= SENSOR_PERIOD) {
                sensCounter = 0;
                sensFlag = 1;
            }
        }

        
        if (motorFlag) {
            motorFlag = 0;
            
            output_high(Motore_dx);
            delay_us(THigh_dx);
            output_low(Motore_dx);
            
            output_high(Motore_sx);
            delay_us(THigh_sx);
            output_low(Motore_sx);
        }

        
        if (sensFlag) {
            sensFlag = 0;
            invia_dati_sensori();
        }

        
        if (kbhit(BT)) {
            int8 ack = getc(BT);
            if (ack == 1) {
                disable_interrupts(INT_TIMER2);
                THigh_dx = make16(getc(BT), getc(BT));
                THigh_sx = make16(getc(BT), getc(BT));
                enable_interrupts(INT_TIMER2);
            }
        }
    }
}
