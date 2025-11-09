import { Header } from "@/components/layout/header";
import useAuth from "@/hooks/use-auth";
import HomePage from "@/pages/homePage";
import LoginPage from "@/pages/loginPage";
import MoviePage from "@/pages/MoviePage";
import RegisterPage from "@/pages/registerPage";
import { Redirect, Route, Switch } from "wouter";

export default function Routes() {
  const auth = useAuth();

  return (
    <div className="w-screen h-screen box-border flex flex-col bg-background text-foreground">
      <Header />
      <Switch>
        <Route path="/auth/login">
          {auth?.isAuth ? <Redirect to="/" /> : <LoginPage />}
        </Route>
        <Route path="/auth/register">
          {auth?.isAuth ? <Redirect to="/" /> : <RegisterPage />}
        </Route>

        <Route path="/movie">
          <MoviePage />
        </Route>

        <Route path="/">
          <HomePage />
        </Route>
      </Switch>
    </div>
  );
}
