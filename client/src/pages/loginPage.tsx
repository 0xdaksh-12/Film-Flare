import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import useAuth from "@/hooks/use-auth";
import { toast } from "sonner";
import { AxiosError } from "axios";

// Zod schema for login form validation
const loginSchema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

// Type for form data (inferred from schema)
type LoginFormData = z.infer<typeof loginSchema>;

// Type for Google OAuth response (placeholder)
interface GoogleLoginResponse {
  credential: string;
}

export default function LoginPage() {
  const auth = useAuth();
  const [, setLocation] = useLocation();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Ensure useAuth is used within AuthProvider
  if (!auth) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  const { login } = auth;

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      await login(data);
      setLocation("/"); // Redirect after login
    } catch (error: unknown) {
      let errorMsg = "Login failed.";
      if (error instanceof AxiosError) {
        errorMsg =
          error.response?.data?.message ||
          error.response?.data?.detail ||
          error.message ||
          "Login failed.";
      } else if (error instanceof Error) {
        errorMsg = error.message;
      }
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  // Placeholder for Google OAuth login
  const onGoogleLogin = async (_response: GoogleLoginResponse) => {
    setIsLoading(true);
    setError(null);

    try {
      console.log({ _response });
      // Placeholder: Implement Google OAuth logic here
      // Example: await handleGoogleLogin(response.credential);
      toast.error("Google login not implemented", {
        description: "Google OAuth functionality is not yet available.",
      });
    } catch (err: unknown) {
      setError((err as Error)?.message || "An error occurred.");
      toast.error("Google login failed", {
        description: (err as Error)?.message || "An error occurred.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-20vh)]">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Welcome Back</CardTitle>
          <CardDescription className="text-center">
            Sign in to continue
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* Email */}
            <div className="gap-2 flex flex-col">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                {...form.register("email")}
              />
              {form.formState.errors.email && (
                <p className="text-red-500 text-sm">
                  {form.formState.errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div className="gap-2 flex flex-col">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                {...form.register("password")}
              />
              {form.formState.errors.password && (
                <p className="text-red-500 text-sm">
                  {form.formState.errors.password.message}
                </p>
              )}
            </div>

            {/* Error message */}
            {error && <p className="text-red-500 text-center">{error}</p>}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Signing in..." : "Sign In"}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">
                Or continue with
              </span>
            </div>
          </div>

          {/* Google login placeholder */}
          <div className="flex justify-center">
            {/* Placeholder for GoogleLogin component */}
            <Button
              variant="outline"
              className="w-full"
              onClick={() =>
                onGoogleLogin({ credential: "placeholder-credential" })
              }
              disabled={isLoading}
            >
              Sign in with Google
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
