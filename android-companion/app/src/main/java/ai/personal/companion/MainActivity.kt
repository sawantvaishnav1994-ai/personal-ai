package ai.personal.companion

import android.os.Bundle
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

class MainActivity: AppCompatActivity() {
  private val client=OkHttpClient(); private var ws:WebSocket?=null
  private lateinit var status:TextView; private lateinit var base:EditText; private lateinit var pairToken:EditText; private lateinit var code:EditText
  private val prefs by lazy { val key=MasterKey.Builder(this).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(); EncryptedSharedPreferences.create(this,"personal_ai_device",key,EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM) }
  override fun onCreate(savedInstanceState:Bundle?){ super.onCreate(savedInstanceState)
    val box=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL; setPadding(32,32,32,32)}
    base=EditText(this).apply{hint="http://PC:8766"; setText(prefs.getString("base","") ?: "")}; pairToken=EditText(this).apply{hint="Pairing token from desktop"}; code=EditText(this).apply{hint="6-digit code"}; status=TextView(this).apply{text="Not paired"}; val pair=Button(this).apply{text="Pair"}; val connect=Button(this).apply{text="Connect"}
    listOf(base,pairToken,code,pair,connect,status).forEach{box.addView(it)}; setContentView(box); pair.setOnClickListener{pairDevice()}; connect.setOnClickListener{connectDevice()}
  }
  private fun pairDevice(){
    val body=JSONObject().put("token",pairToken.text.toString()).put("code",code.text.toString()).put("name",android.os.Build.MODEL).put("platform","android").toString().toRequestBody("application/json".toMediaType()); val req=Request.Builder().url(base.text.toString().trimEnd('/')+"/pair/confirm").post(body).build()
    client.newCall(req).enqueue(object:Callback{
      override fun onFailure(call:Call,e:IOException){runOnUiThread{status.text="Pair failed: ${e.message}"}}
      override fun onResponse(call:Call,response:Response){response.use{val text=it.body?.string().orEmpty(); if(!it.isSuccessful){runOnUiThread{status.text="Pair failed: $text"};return}; val obj=JSONObject(text); val device=obj.getJSONObject("device").getString("id"); val bearer=obj.getString("bearer_token"); prefs.edit().putString("base",base.text.toString()).putString("device",device).putString("bearer",bearer).apply(); runOnUiThread{status.text="Paired as $device"}}}
    })
  }
  private fun connectDevice(){
    val device=prefs.getString("device",null); val bearer=prefs.getString("bearer",null); if(device==null||bearer==null){status.text="Pair first";return}; val wsUrl=base.text.toString().replaceFirst("http://","ws://").replaceFirst("https://","wss://").trimEnd('/')+"/device/ws/$device"; val req=Request.Builder().url(wsUrl).addHeader("Authorization","Bearer $bearer").build(); ws=client.newWebSocket(req,object:WebSocketListener(){
      override fun onOpen(webSocket:WebSocket,response:Response){runOnUiThread{status.text="Connected"}; webSocket.send(JSONObject().put("type","hello").put("device_id",device).toString())}
      override fun onMessage(webSocket:WebSocket,text:String){runOnUiThread{status.text=text.take(300)}}
      override fun onFailure(webSocket:WebSocket,t:Throwable,response:Response?){runOnUiThread{status.text="Error: ${t.message}"}}
    })
  }
  override fun onDestroy(){ws?.close(1000,"bye");super.onDestroy()}
}
