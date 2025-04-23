'use client';
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Message } from './Message';

export default function ChatWindow() {
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<[string,string][]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  const send = async () => {
    if (!input) return;
    const userMsg = input;
    setHistory([...history, [userMsg, '']]);
    setInput('');
    const res = await axios.post(
      `${process.env.NEXT_PUBLIC_API_URL}/chat`,
      { message: userMsg, history }
    );
    setHistory(res.data.history);
  };

  useEffect(() => {
    containerRef.current?.scrollTo({ top: containerRef.current.scrollHeight });
  }, [history]);

  return (
    <div className="flex flex-col flex-1 border rounded-lg p-4">
      <div ref={containerRef} className="overflow-y-auto flex-1 mb-4">
        {history.map(([u, b], i) => (
          <div key={i}>
            <Message fromUser text={u} />
            <Message text={b} />
          </div>
        ))}
      </div>
      <div className="flex">
        <input
          className="flex-1 p-2 border rounded-l-lg"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Type a message..."
        />
        <button
          className="bg-blue-600 text-white px-4 rounded-r-lg"
          onClick={send}
        >Send</button>
      </div>
    </div>
  );
}