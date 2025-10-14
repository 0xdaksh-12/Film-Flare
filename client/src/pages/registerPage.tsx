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

// Zod schema for register form validation
const registerSchema = z
  .object({
    fullName: z.string().min(2, "Full name must be at least 2 characters"),
    email: z.email("Invalid email"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    path: ["confirmPassword"],
    message: "Passwords do not match",
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const auth = useAuth();
  const [, setLocation] = useLocation();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  if (!auth) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  const { register: signup, loading: authLoading } = auth;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      fullName: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    setError(null);
    try {
      await signup({
        name: data.fullName,
        email: data.email,
        password: data.password,
      });
      setLocation("/");
    } catch (err: unknown) {
      let errorMsg = "Registration failed.";
      if (err instanceof AxiosError) {
        errorMsg =
          err.response?.data?.message ||
          err.response?.data?.detail ||
          err.message ||
          "Registration failed.";
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const onGoogleSignup = async () => {
    setIsLoading(true);
    setError(null);
    try {
      toast.error("Google signup not implemented", {
        description: "Google OAuth functionality is not yet available.",
      });
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error ? err.message : "An error occurred.";
      setError(errorMsg);
      toast.error("Google signup failed", { description: errorMsg });
    } finally {
      setIsLoading(false);
    }
  };

  const isDisabled = isLoading || authLoading;

  return (
    <div className="flex items-center justify-center min-h-[90vh]">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Create Account</CardTitle>
          <CardDescription className="text-center">
            Sign up to get started
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                placeholder="User Name"
                {...register("fullName")}
                disabled={isDisabled}
              />
              {errors.fullName && (
                <p className="text-red-500 text-sm">
                  {errors.fullName.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                autoComplete="off"
                {...register("email")}
                disabled={isDisabled}
              />
              {errors.email && (
                <p className="text-red-500 text-sm">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="At least 6 characters"
                autoComplete="new-password"
                {...register("password")}
                disabled={isDisabled}
              />
              {errors.password && (
                <p className="text-red-500 text-sm">
                  {errors.password.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Re-enter your password"
                autoComplete="new-password"
                {...register("confirmPassword")}
                disabled={isDisabled}
              />
              {errors.confirmPassword && (
                <p className="text-red-500 text-sm">
                  {errors.confirmPassword.message}
                </p>
              )}
            </div>

            {error && <p className="text-red-500 text-center">{error}</p>}

            <Button type="submit" className="w-full" disabled={isDisabled}>
              {isDisabled ? "Creating account..." : "Create Account"}
            </Button>
          </form>

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

          <Button
            variant="outline"
            className="w-full"
            onClick={onGoogleSignup}
            disabled={isDisabled}
          >
            Sign up with Google
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
