const express = require('express');
const app = express();
app.use(express.json());

// In-memory data store
let users = [
  { id: 1, name: 'Alice', email: 'alice@example.com' },
  { id: 2, name: 'Bob', email: 'bob@example.com' }
];
let nextId = 3;

// GET all users
app.get('/api/users', (req, res) => {
  const { limit = 10, offset = 0 } = req.query;
  const paginatedUsers = users.slice(offset, offset + parseInt(limit));
  res.json({
    users: paginatedUsers,
    total: users.length,
    limit: parseInt(limit),
    offset: parseInt(offset)
  });
});

// GET user by ID
app.get('/api/users/:id', (req, res) => {
  const user = users.find(u => u.id === parseInt(req.params.id));
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }
  res.json(user);
});

// POST create new user
app.post('/api/users', (req, res) => {
  const { name, email } = req.body;
  
  if (!name || !email) {
    return res.status(400).json({ error: 'Name and email are required' });
  }
  
  const newUser = {
    id: nextId++,
    name,
    email
  };
  
  users.push(newUser);
  res.status(201).json(newUser);
});

// PUT update user
app.put('/api/users/:id', (req, res) => {
  const userId = parseInt(req.params.id);
  const userIndex = users.findIndex(u => u.id === userId);
  
  if (userIndex === -1) {
    return res.status(404).json({ error: 'User not found' });
  }
  
  const { name, email } = req.body;
  if (!name || !email) {
    return res.status(400).json({ error: 'Name and email are required' });
  }
  
  users[userIndex] = { id: userId, name, email };
  res.json(users[userIndex]);
});

// DELETE user
app.delete('/api/users/:id', (req, res) => {
  const userId = parseInt(req.params.id);
  const userIndex = users.findIndex(u => u.id === userId);
  
  if (userIndex === -1) {
    return res.status(404).json({ error: 'User not found' });
  }
  
  users.splice(userIndex, 1);
  res.status(204).send();
});

// New endpoint - will trigger test evolution
app.get('/api/users/search', (req, res) => {
  const { query } = req.query;
  if (!query) {
    return res.status(400).json({ error: 'Query parameter is required' });
  }
  
  const results = users.filter(u => 
    u.name.toLowerCase().includes(query.toLowerCase()) ||
    u.email.toLowerCase().includes(query.toLowerCase())
  );
  
  res.json({ results, query });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Sample API server running on port ${PORT}`);
});