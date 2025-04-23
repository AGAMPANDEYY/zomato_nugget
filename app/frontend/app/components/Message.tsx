interface MessageProps { text: string; fromUser?: boolean; }
export function Message({ text, fromUser = false }: MessageProps) {
  return (
    <div className={`flex ${fromUser ? 'justify-end' : 'justify-start'} mb-2`}>      
      <div className={`${fromUser ? 'bg-blue-500 text-white' : 'bg-white'} p-3 rounded-2xl shadow max-w-xs`}>{text}</div>
    </div>
  );
}