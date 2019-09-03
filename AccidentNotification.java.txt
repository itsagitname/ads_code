package projectwork.daiict.vismay.mybike;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.AsyncTask;
import android.os.CountDownTimer;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.os.SystemClock;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.telephony.SmsManager;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InterruptedIOException;
import java.io.OutputStream;
import java.util.Calendar;
import java.util.TimeZone;
import java.util.Timer;
import java.util.TimerTask;
import java.util.UUID;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadPoolExecutor;

public class AccidentNotification extends AppCompatActivity {
    private TextView textView5, textView6;
    private Button button5;
    private Boolean inmotion = false, firstrunn = true, fuelrequest = false, driveroadrequest = false, fuelread = false, driveroadread = false, drven = true;
    private Boolean flag = true, storeindevice = true;
    private static String ridername = null, riderno = null, devicemacid = null, latitude_data = "Latitude", longitude_data = "Longitude", speed_data = "Speed";
    private static String drivestyle = "Soft Braking", devicename = null, datetime0 = null, acctype = "None";
    private static double totdist = 0, totdist1 = 0, totdist2 = 0, speed_value =0, speedmaxm = 0, speedavg = 0, latitude_value = 0, longitude_value = 0, lat0 = 0, long0 = 0;
    private static double fuelcost = 0;
    private static long t0 = 0, tfirst = 0, time_value = 0;
    private static String parentref = null, childref = null, filname = null, mileage = null, fuelprice = null;
    private static int childno = 1;
    private Handler myhandler = null;
    private Runnable watchdog_run = null, sms_run = null;
    private PowerManager.WakeLock wakeLock = null;
    private Calendar c;
    private File file = null;
    private CountDownTimer watchdogtimer = null;
    private ThreadPoolExecutor executor1 = null;
    private Timer t = null;
    private TimerTask tsk = null;
    private LocationManager locationMangaer = null;
    private LocationListener locationListener = null;
    private Looper loop1 = null;
    private BluetoothAdapter mBluetoothAdapter = null;
    private BluetoothSocket mmSocket = null;
    private BluetoothDevice mmDevice = null;
    private InputStream mmInputStream = null;
    private OutputStream mmOutputStream = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_dashboard);
        textView5 = (TextView) findViewById(R.id.textView5);
        textView6 = (TextView) findViewById(R.id.textView6);
        button5 = (Button) findViewById(R.id.button5);
        button5.setEnabled(false);

        SharedPreferences sp = getSharedPreferences("globpref", 0);
        ridername = sp.getString("ridername","");
        riderno = sp.getString("riderno","");
        devicename = sp.getString("devname","");
        devicemacid = sp.getString("devmacid","");
        mileage = sp.getString("mileage","");
        fuelprice = sp.getString("fuelprice","");
        parentref = sp.getString("parentref",""); // this should be commited back to sharedpreferences when device gets disconncted i.e at end of trip
        childno = sp.getInt("childno",0); // this should be commited back to sharedpreferences when device gets disconncted i.e at end of trip
        textView5.setText("Connected");
        textView6.setText(devicename);
        PowerManager mgr = (PowerManager) getSystemService(Context.POWER_SERVICE);
        wakeLock = mgr.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"MyWakeLock");

        c = Calendar.getInstance(TimeZone.getTimeZone("GMT+5:30"));
        int mnth = c.get(Calendar.MONTH) + 1;
        String currentref = c.get(Calendar.DATE)+ "-" + mnth + "-" + c.get(Calendar.YEAR);
        if(!parentref.equals(currentref)) {
            parentref = currentref;
            childno = 1;
        }
        childref = "TRIP" + childno;
        filname = parentref + "_" + childref + ".txt";
        file = new File(getApplicationContext().getFilesDir(), filname);

        executor1= (ThreadPoolExecutor) Executors.newCachedThreadPool();
        myhandler = new Handler(getApplicationContext().getMainLooper());
        watchdog_run = new Runnable() {
            @Override
            public void run() {
                t = new Timer();
                tsk = new TimerTask() {
                    @Override
                    public void run() {
                        inmotion = false;
                    }
                };
               t.schedule(tsk,12000);
            }
        };

        sms_run = new Runnable() {
            @Override
            public void run() {
                new sms_sending().execute();
            }
        };
        wakeLock.acquire();
        //start the threadpool exection of two giants
        executor1.execute(new gps_run());
        executor1.execute(new bt_run());
        //end of threadpool code

        // initiate broadcast receiver to receive bluetooth disconnection and correspondingly flag = false if disconnected.
        IntentFilter BT_Search = new IntentFilter();
        BT_Search.addAction(BluetoothDevice.ACTION_ACL_DISCONNECTED);
        BroadcastReceiver receive1 = new myreceiver();
        registerReceiver(receive1,BT_Search);
        // broadcast receiver code ends

        button5.setOnClickListener(new OnClickListener() {
            public void onClick(View v) {
                // initiating data uploading to the firebase and store in text file
                if(storeindevice) {
                    String tmpdata = "Distance Travelled: " + (totdist/1000.0) + " km" + "\n" + "Top Speed: " + speedmaxm + " km/h" + "\n" + "Average Speed: " + speedavg + " km/h";
                    String tmpdata1 = tmpdata + "\n" + "Ideal Fuel Cost: " + fuelcost + " Rs" + "\n" + "Overall Road Condition: " + roadstyle + "\n" + "Overall Driving Style: " + drivestyle + "\n";
                    try {
                        FileOutputStream outputStream1 = new FileOutputStream(file,true);
                        // FileOutputStream outputStream = openFileOutput(filname, Context.MODE_PRIVATE);
                        outputStream1.write(tmpdata1.getBytes());
                        outputStream1.close();
                        storeindevice = false;
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }
                // code for uploading on Firebase and show progressbar...if not uploaded succesfully then give another chance otherwise disable button5.

                // end of code
            }
        });

    }

  /*  private void sendSMS(String riderno, String msgbody)
    {
        SmsManager smsmngr = SmsManager.getDefault();
        smsmngr.sendTextMessage(riderno, null, msgbody, null, null);
    } */

    private class myreceiver extends BroadcastReceiver {

        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if(BluetoothDevice.ACTION_ACL_DISCONNECTED.equals(action)) {
                BluetoothDevice device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
                if(device.getAddress().equals(devicemacid)) {
                    // termination code here..
                    flag = false;
                    button5.setEnabled(true);
                }
            }
        }
    }

    private class gps_run implements  Runnable {
        @Override
        public void run() {
            try {
                locationListener = new MyLocationListener();
                loop1 = Looper.myLooper();
                loop1.prepare();
                locationMangaer.requestLocationUpdates(LocationManager.NETWORK_PROVIDER, 0, 60, locationListener,loop1);
                loop1.loop();
            }
            catch (IllegalArgumentException | NullPointerException | SecurityException e) {
                e.printStackTrace();
            }
        }
    }

    private class bt_run implements  Runnable {
        @Override
        public void run() {
            mmDevice = mBluetoothAdapter.getRemoteDevice(devicemacid);
            UUID uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"); //Standard SerialPortService ID

            try{
                mmSocket = mmDevice.createRfcommSocketToServiceRecord(uuid);
                mmSocket.connect();
                mmInputStream = mmSocket.getInputStream();
                mmOutputStream = mmSocket.getOutputStream();
            }

            catch (IOException e){
                e.printStackTrace();
                return;
            }

            while(flag)
            {
                try
                {
                    int bytesAvailable = mmInputStream.available();
                    if(bytesAvailable > 0)
                    {
                        byte[] packetBytes = new byte[bytesAvailable];
                        int temp = mmInputStream.read(packetBytes,0,3);
                        // start checking
                        if(packetBytes[0] == 67) {
                            //prepare sms body and initiate sms service
                            acctype = "Collision";
                            myhandler.post(sms_run);
                        }
                        else if(packetBytes[0] == 70 && inmotion) {
                            //prepare sms body and initiate sms service
                            acctype = "Fall";
                            myhandler.post(sms_run);
                        }
                        else if(driveroadread) {
                            if(packetBytes[1] == 82)  {
                                drivestyle = "Hard Braking";
                            }
                            if(packetBytes[1] == 70) {
                                drivestyle = "Normal Braking";
                            }
                            driveroadread = false;
                            if("Hard Braking".equals(drivestyle) {
                                drven = false;
                            }
                        }
                    }
                    if(driveroadrequest) {
                        String msg = "S";
                        driveroadread = true;
                        driveroadrequest = false;
                        mmOutputStream.write(msg.getBytes());
                    }
                }
                catch (IOException ex)
                {
                    // get to sleep for 1 second !
                    try {
                        Thread.sleep(1000);
                    }
                    catch(InterruptedException ex1){
                        Thread.currentThread().interrupt();
                    }
                }
                try {
                    Thread.sleep(100);
                }
                catch(InterruptedException ex2){
                    Thread.currentThread().interrupt();
                }
            }
        }
    }

    private class MyLocationListener implements LocationListener {
        @Override
        public void onLocationChanged(Location loc) {

            if(flag) {
                if(inmotion) {
                    t.cancel();
                }
                latitude_value = loc.getLatitude();
                longitude_value = loc.getLongitude();
                // time_value = loc.getElapsedRealtimeNanos();
                time_value = SystemClock.elapsedRealtime(); //in milliseconds
                float[] dist = new float[1];
                if(firstrunn) {
                    lat0 = latitude_value;
                    long0 = longitude_value;
                    tfirst = time_value;
                    datetime0 = "" + c.getTime(); // datetime at which trip started
                    //push lat and long to text file
                    String pointdata1 = latitude_data + "," + longitude_data + "\n";
                    try {
                        FileOutputStream outputStream1 = new FileOutputStream(file,true);
                        // FileOutputStream outputStream = openFileOutput(filname, Context.MODE_PRIVATE);
                        outputStream1.write(pointdata1.getBytes());
                        outputStream1.close();
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }
                Location.distanceBetween(lat0, long0, latitude_value, longitude_value, dist);
                totdist = totdist + (double)dist[0];
                totdist1 = totdist1 + (double)dist[0];
                totdist2 = totdist2 + (double)dist[0];

                speed_value = 3600.0 * ((double)dist[0] /(time_value-t0)); // in km/h
                if(speed_value > speedmaxm)
                    speedmaxm = speed_value; //gives maximum speed
                if(firstrunn) {
                    speedavg = speed_value; //gives average speed
                }
                else {
                    speedavg = (3600.0) * (totdist/(time_value-tfirst)); // in km/h
                }

                firstrunn = false;
                latitude_data = "" + Math.round(latitude_value * 1000000.0)/1000000.0;
                longitude_data = "" + Math.round(longitude_value * 1000000.0)/1000000.0;
                speed_data = "" + Math.round(speed_value * 100.0)/100.0;

                // if totdist1 becomes 500 m then push co-ordinates into text file
                if(totdist1 > 500) {
                    // do push co-ordinates into a text file: String pointdata = latitude_data + "," + longitude_data + "\n";
                    String pointdata = latitude_data + "," + longitude_data + "\n";
                    try {
                        FileOutputStream outputStream = new FileOutputStream(file,true);
                        // FileOutputStream outputStream = openFileOutput(filname, Context.MODE_PRIVATE);
                        outputStream.write(pointdata.getBytes());
                        outputStream.close();
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                    totdist1 = 0;
                }
                // if totdist2 becomes 1 km or 1000 m then call for sensor to get driving style and totdist2 = 0
                else if(totdist2 > 1000 && drven) {
                    driveroadrequest = true;
                    totdist2 = 0;
                }

                lat0 = latitude_value;
                long0 = longitude_value;
                t0 = time_value;
                inmotion = true;
                myhandler.post(watchdog_run);
            }
        }
        @Override
        public void onProviderDisabled(String provider) {
        }

        @Override
        public void onProviderEnabled(String provider) {
        }

        @Override
        public void onStatusChanged(String provider,int status, Bundle extras) {
        }

    }

    private class sms_sending extends AsyncTask<Void,Void,Void> {
        @Override
        protected Void doInBackground(Void... params) {
           try {
              // sendSMS(riderno, msgbody);
               int mnth = c.get(Calendar.MONTH) + 1;
               String dt = c.get(Calendar.DATE)+ "/" + mnth + "/" + c.get(Calendar.YEAR);
               String tm = c.get(Calendar.HOUR_OF_DAY) + ":" + c.get(Calendar.MINUTE) + ":" + c.get(Calendar.SECOND);
               String msgbody = dt + "," + tm + "\n" + ridername + ","+ devicename + "\n" + acctype + "," + speed_data + " km/h" + "\n" + "https://maps.google.co.in/maps?&z=15&mrt=yp&t=k&q=" + latitude_data + "+" + longitude_data ;
               SmsManager smsmngr = SmsManager.getDefault();
               smsmngr.sendTextMessage(riderno, null, msgbody, null, null);
           }
           catch (Exception e) {
               Toast.makeText(getApplicationContext(),"Accident Detected !",Toast.LENGTH_SHORT).show();
           }
            return null;
        }

        @Override
        protected void onPostExecute(Void aVoid) {
            super.onPostExecute(aVoid);
            Toast.makeText(getApplicationContext(),"Accident Detected !",Toast.LENGTH_SHORT).show();
        }
    }

}
