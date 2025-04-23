import './globals.css';
import { ReactNode } from 'react';

export const metadata = {
  title: 'Zomato RAG Chatbot',
  description: 'Ask anything about restaurants',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900">
        <main className="container mx-auto p-4 h-screen flex flex-col">
          <h1 className="text-3xl font-bold mb-4">Zomato RAG Chatbot</h1>
          {children}
        </main>
      </body>
    </html>
  );
}