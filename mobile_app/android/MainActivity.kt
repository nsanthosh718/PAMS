package com.pams.athlete

import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import android.webkit.WebSettings
import androidx.appcompat.app.AppCompatActivity
import android.view.View
import android.widget.ProgressBar

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private lateinit var progressBar: ProgressBar
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        webView = findViewById(R.id.webview)
        progressBar = findViewById(R.id.progressBar)
        
        setupWebView()
        loadApp()
    }
    
    private fun setupWebView() {
        val webSettings: WebSettings = webView.settings
        webSettings.javaScriptEnabled = true
        webSettings.domStorageEnabled = true
        webSettings.allowFileAccess = false
        webSettings.allowContentAccess = false
        webSettings.allowFileAccessFromFileURLs = false
        webSettings.allowUniversalAccessFromFileURLs = false
        
        webView.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
                progressBar.visibility = View.VISIBLE
            }
            
            override fun onPageFinished(view: WebView?, url: String?) {
                progressBar.visibility = View.GONE
            }
            
            override fun onReceivedError(view: WebView?, request: android.webkit.WebResourceRequest?, error: android.webkit.WebResourceError?) {
                val errorHtml = """
                    <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
                        <h2>📱 PAMS Offline</h2>
                        <p>Please check your internet connection</p>
                        <button onclick="location.reload()">Retry</button>
                    </body></html>
                """
                webView.loadDataWithBaseURL(null, errorHtml, "text/html", "UTF-8", null)
            }
        }
    }
    
    private fun loadApp() {
        webView.loadUrl("https://your-pams-app.herokuapp.com/mobile")
    }
    
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}