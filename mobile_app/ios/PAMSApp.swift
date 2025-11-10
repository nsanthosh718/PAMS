import SwiftUI
import WebKit

@main
struct PAMSApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    @State private var showingSplash = true
    
    var body: some View {
        if showingSplash {
            SplashView()
                .onAppear {
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                        showingSplash = false
                    }
                }
        } else {
            WebView()
        }
    }
}

struct SplashView: View {
    var body: some View {
        ZStack {
            LinearGradient(
                gradient: Gradient(colors: [Color.blue, Color.purple]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            VStack {
                Text("⚽")
                    .font(.system(size: 80))
                
                Text("PAMS")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                    .foregroundColor(.white)
                
                Text("Predictable Excellence")
                    .font(.subheadline)
                    .foregroundColor(.white.opacity(0.8))
            }
        }
    }
}

struct WebView: UIViewRepresentable {
    let url = URL(string: "https://your-pams-app.herokuapp.com/mobile")!
    
    func makeUIView(context: Context) -> WKWebView {
        let webView = WKWebView()
        webView.navigationDelegate = context.coordinator
        
        webView.configuration.preferences.javaScriptEnabled = true
        webView.configuration.allowsInlineMediaPlayback = true
        
        let request = URLRequest(url: url)
        webView.load(request)
        
        return webView
    }
    
    func updateUIView(_ uiView: WKWebView, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator: NSObject, WKNavigationDelegate {
        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            let html = """
            <html><body style="font-family: -apple-system; text-align: center; padding: 50px;">
                <h2>📱 PAMS Offline</h2>
                <p>Check internet connection</p>
                <button onclick="location.reload()">Retry</button>
            </body></html>
            """
            webView.loadHTMLString(html, baseURL: nil)
        }
    }
}