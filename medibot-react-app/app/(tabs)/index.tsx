import React, { useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

export default function HomeScreen() {
  const [input, setInput] = useState('');
  const [chat, setChat] = useState([]);
  const scrollViewRef = useRef();

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { role: 'user', content: input };
    setChat(prev => [...prev, userMsg]);
    setInput('');

    try {
      const res = await fetch('https://medibot-backend-ylqu.onrender.com/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMsg.content }),
      });

      const data = await res.json();
      if (data.answer) {
        const botMsg = { role: 'bot', content: data.answer };
        setChat(prev => [...prev, botMsg]);
      } else {
        throw new Error("No answer from server");
      }
    } catch (err) {
      setChat(prev => [...prev, { role: 'bot', content: '❌ Failed to connect to server.' }]);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.select({ ios: 'padding' })}>
      <View style={styles.header}>
        <Text style={styles.headerText}>🤖 MediBot</Text>
      </View>

      <ScrollView
        ref={scrollViewRef}
        style={styles.chatContainer}
        contentContainerStyle={{ paddingBottom: 20 }}
        onContentSizeChange={() => scrollViewRef.current.scrollToEnd({ animated: true })}
      >
        {chat.map((msg, index) => (
          <View key={index} style={[styles.messageContainer, msg.role === 'user' ? styles.user : styles.bot]}>
            <Text style={styles.messageText}>{msg.content}</Text>
          </View>
        ))}
      </ScrollView>

      <View style={styles.inputRow}>
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder="Type your message..."
          style={styles.input}
        />
        <TouchableOpacity onPress={sendMessage} style={styles.sendButton}>
          <Text style={styles.sendText}>SEND</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f6fa',
    paddingHorizontal: 10,
    paddingTop: 40,
  },
  header: {
    padding: 15,
    backgroundColor: '#007bff',
    alignItems: 'center',
    marginBottom: 10,
    borderRadius: 10,
  },
  headerText: {
    color: '#fff',
    fontSize: 22,
    fontWeight: 'bold',
  },
  chatContainer: {
    flex: 1,
  },
  messageContainer: {
    maxWidth: '80%',
    padding: 10,
    marginVertical: 5,
    borderRadius: 16,
  },
  user: {
    backgroundColor: '#d1ffd6',
    alignSelf: 'flex-end',
  },
  bot: {
    backgroundColor: '#f0f0f0',
    alignSelf: 'flex-start',
  },
  messageText: {
    fontSize: 16,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderTopWidth: 1,
    borderColor: '#ddd',
    padding: 10,
    backgroundColor: '#fff',
  },
  input: {
    flex: 1,
    backgroundColor: '#eee',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 16,
  },
  sendButton: {
    marginLeft: 8,
    backgroundColor: '#007bff',
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 14,
  },
  sendText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});
