import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import Routes from "./routes";
import AuthProvider from "./provider/authProvider";

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem={true}>
      <AuthProvider>
        <Toaster position="bottom-right" />
        <Routes />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
