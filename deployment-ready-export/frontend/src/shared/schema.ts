// Re-export everything from types.ts for compatibility
export * from "./types";
// Additional schema definitions
import { z } from "zod";
export const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});
export const insertUserSchema = z.object({
  username: z.string().min(3, "Username must be at least 3 characters"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  email: z.string().email("Valid email is required").optional(),
});
export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof insertUserSchema>;
