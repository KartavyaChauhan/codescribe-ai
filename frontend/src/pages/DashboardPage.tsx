import { useState } from "react";
import { useAuthStore } from "../store/authStore";
import { analyzeRepo, queryRepo } from "../api";

interface Message {
    sender: 'user' | 'ai';
    text: string;
}

const DashboardPage = () => {
    const token = useAuthStore((state) => state.token);
    const logout = useAuthStore((state) => state.logout);

    const [repoUrl, setRepoUrl] = useState("");
    const [question, setQuestion] = useState("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const handleAnalyze = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!repoUrl || !token) return;
        setIsLoading(true);
        setMessages([]); // Clear chat on new analysis
        try {
            const res = await analyzeRepo({ repo_url: repoUrl }, token);
            setMessages([{ sender: 'ai', text: res.message || "Repository analyzed successfully. Ask me anything!" }]);
        } catch (error) {
            console.error(error);
            setMessages([{ sender: 'ai', text: "Error analyzing repository. Please check the URL and try again." }]);
        }
        setIsLoading(false);
    };

    const handleQuery = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!question || !token) return;
        const newMessages: Message[] = [...messages, { sender: 'user', text: question }];
        setMessages(newMessages);
        setQuestion("");
        setIsLoading(true);

        try {
            const res = await queryRepo({ question }, token);
            setMessages([...newMessages, { sender: 'ai', text: res.answer }]);
        } catch (error) {
            console.error(error);
            setMessages([...newMessages, { sender: 'ai', text: "Sorry, I encountered an error. Please try again." }]);
        }
        setIsLoading(false);
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white flex flex-col p-4">
            <div className="container mx-auto">
                <header className="flex justify-between items-center mb-4 pb-4 border-b border-gray-700">
                    <h1 className="text-3xl font-bold text-cyan-400">CodeScribe AI</h1>
                    <button onClick={logout} className="px-4 py-2 font-semibold text-white bg-red-600 rounded-md hover:bg-red-700">
                        Logout
                    </button>
                </header>

                <main className="flex-grow flex flex-col">
                    <form onSubmit={handleAnalyze} className="flex gap-2 mb-4">
                        <input
                            type="text"
                            value={repoUrl}
                            onChange={(e) => setRepoUrl(e.target.value)}
                            placeholder="Enter GitHub Repository URL to Analyze"
                            className="flex-grow p-2 bg-gray-800 border border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        />
                        <button type="submit" disabled={isLoading} className="px-4 py-2 bg-cyan-600 rounded-md hover:bg-cyan-700 disabled:bg-gray-500">
                            {isLoading ? 'Analyzing...' : 'Analyze'}
                        </button>
                    </form>

                    <div className="flex-grow bg-gray-800 rounded-lg p-4 mb-4 overflow-y-auto h-96 flex flex-col gap-4">
                        {messages.map((msg, index) => (
                            <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <p className={`max-w-xl p-3 rounded-lg ${msg.sender === 'user' ? 'bg-cyan-800' : 'bg-gray-700'}`}>
                                    {msg.text}
                                </p>
                            </div>
                        ))}
                        {isLoading && <p className="text-center text-gray-400">AI is thinking...</p>}
                    </div>

                    <form onSubmit={handleQuery} className="flex gap-2">
                        <input
                            type="text"
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            placeholder="Ask a question about the repository..."
                            className="flex-grow p-2 bg-gray-800 border border-gray-700 rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        />
                        <button type="submit" disabled={isLoading} className="px-4 py-2 bg-cyan-600 rounded-md hover:bg-cyan-700 disabled:bg-gray-500">
                            Ask
                        </button>
                    </form>
                </main>
            </div>
        </div>
    );
};

export default DashboardPage;
