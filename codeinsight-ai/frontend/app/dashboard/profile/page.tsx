"use client";

import { useRouter } from "next/navigation";
import { LogOut, Trash2, UserCircle } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";
import { deleteAccount } from "@/lib/api";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  function handleLogout() {
    logout();
    router.push("/");
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteAccount();
      logout();
      router.push("/");
    } catch {
      setDeleting(false);
    }
  }

  if (!user) return null;

  return (
    <div className="max-w-lg">
      <h1 className="mb-1 font-display text-2xl font-semibold tracking-tight">Profile</h1>
      <p className="mb-8 text-sm text-muted-foreground">Your account.</p>

      <Card className="mb-5">
        <CardContent className="flex items-center gap-4 p-6">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-primary to-accent text-lg font-medium text-white">
            {(user.email[0] ?? "?").toUpperCase()}
          </div>
          <div>
            <p className="font-medium">{user.email}</p>
            <p className="text-xs text-muted-foreground">
              Joined {new Date(user.created_at).toLocaleDateString()}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card className="mb-5">
        <CardContent className="flex items-center justify-between p-5">
          <p className="text-sm">Sign out of your account</p>
          <Button variant="outline" size="sm" onClick={handleLogout}>
            <LogOut className="h-4 w-4" /> Sign out
          </Button>
        </CardContent>
      </Card>

      <Card className="border-red-500/30">
        <CardContent className="flex items-center justify-between p-5">
          <div>
            <p className="text-sm">Delete account</p>
            <p className="text-xs text-muted-foreground">Permanently removes your account and all reviews.</p>
          </div>
          {!confirmDelete ? (
            <Button variant="outline" size="sm" onClick={() => setConfirmDelete(true)}>
              <Trash2 className="h-4 w-4" /> Delete
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(false)}>Cancel</Button>
              <Button size="sm" onClick={handleDelete} disabled={deleting} className="bg-red-600 hover:bg-red-500">
                Confirm
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
