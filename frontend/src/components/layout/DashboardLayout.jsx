import React from "react";

export function DashboardLayout({ header, sidebar, children, footer }) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b bg-card/80 backdrop-blur supports-[backdrop-filter]:bg-card/60">{header}</header>
      <div className="flex flex-1 flex-col gap-4 p-4 lg:flex-row">
        <aside className="lg:w-80 lg:flex-shrink-0">{sidebar}</aside>
        <main className="flex-1 space-y-4">{children}</main>
      </div>
      {footer ? <footer className="border-t p-4 text-sm text-muted-foreground">{footer}</footer> : null}
    </div>
  );
}
