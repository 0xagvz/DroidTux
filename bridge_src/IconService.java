package com.droidtux.bridge;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.drawable.Drawable;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;

/**
 * Servicio de extracción de iconos para DroidTux.
 * Convierte cualquier icono de Android (Adaptive, Legacy, etc.) en un PNG de 512x512.
 */
public class IconService extends Service {
    private static final String TAG = "DroidTuxBridge";

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String packageName = intent.getStringExtra("package");
        if (packageName != null) {
            extractIcon(packageName);
        }
        stopSelf();
        return START_NOT_STICKY;
    }

    private void extractIcon(String pkg) {
        try {
            PackageManager pm = getPackageManager();
            Drawable drawable = pm.getApplicationIcon(pkg);
            
            // Renderizar el drawable a un Bitmap de 512x512
            Bitmap bitmap = Bitmap.createBitmap(512, 512, Bitmap.Config.ARGB_8888);
            Canvas canvas = new Canvas(bitmap);
            drawable.setBounds(0, 0, canvas.getWidth(), canvas.getHeight());
            drawable.draw(canvas);

            // Guardar en la carpeta pública (Download) para que ADB pueda hacer pull
            File outFile = new File("/sdcard/Download/" + pkg + ".png");
            FileOutputStream out = new FileOutputStream(outFile);
            bitmap.compress(Bitmap.CompressFormat.PNG, 100, out);
            out.close();
            
            Log.d(TAG, "Icono extraído con éxito para: " + pkg);
        } catch (Exception e) {
            Log.e(TAG, "Error extrayendo icono para " + pkg + ": " + e.getMessage());
        }
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onCreate() {
        super.onCreate();
        // Android 8+ requiere notificación para servicios en primer plano
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel("dt", "DroidTux", NotificationManager.IMPORTANCE_LOW);
            getSystemService(NotificationManager.class).createNotificationChannel(channel);
            startForeground(1, new Notification.Builder(this, "dt").setContentTitle("Extrayendo icono...").build());
        }
    }
}
