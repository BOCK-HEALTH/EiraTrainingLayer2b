# 🤝 Contributing to BOCK Scraper

Thank you for your interest in contributing to BOCK Scraper! This document provides guidelines and instructions for contributing.

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Coding Standards](#coding-standards)
5. [Pull Request Process](#pull-request-process)

---

## 🤗 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Keep discussions professional

---

## 💡 How Can I Contribute?

### Reporting Bugs
- Use GitHub Issues
- Include detailed steps to reproduce
- Provide error messages and logs
- Specify your OS, Python version, and setup

### Suggesting Features
- Check existing issues first
- Explain the use case clearly
- Provide examples if possible
- Consider implementation complexity

### Improving Documentation
- Fix typos and clarify instructions
- Add examples and tutorials
- Translate to other languages
- Create video guides

### Writing Code
- Fix bugs
- Implement new features
- Improve performance
- Add tests

---

## 🔧 Development Setup

### 1. Fork and Clone
```bash
# Fork the repo on GitHub
git clone https://github.com/your-username/bock-scraper.git
cd bock-scraper
```

### 2. Create Virtual Environment
```bash
python -m venv web_venv
source web_venv/bin/activate  # Linux/Mac
web_venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r ec2_files/requirements.txt
pip install -r summary/bocksummarizer-main/requirements.txt
```

### 4. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

### 5. Make Your Changes
- Edit the relevant files
- Test thoroughly
- Add comments where needed

### 6. Test Your Changes
```bash
# Test the web server
python web_server.py

# Test scraping
python ec2_files/ultimate_scraper_v2.py "https://www.bbc.com/news" --max-articles 3

# Verify all features work
```

---

## 📝 Coding Standards

### Python Style
- Follow **PEP 8** style guide
- Use **4 spaces** for indentation
- Maximum line length: **100 characters**
- Use descriptive variable names

### Documentation
```python
def function_name(param1, param2):
    """
    Brief description of what the function does.
    
    Args:
        param1 (type): Description
        param2 (type): Description
        
    Returns:
        type: Description
    """
    pass
```

### Naming Conventions
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_CASE`
- **Private methods**: `_leading_underscore`

### Comments
```python
# Good: Explains WHY
# Calculate relevance score based on URL patterns and metadata
score = calculate_relevance(url, metadata)

# Avoid: Explains WHAT (code should be self-explanatory)
# Add 10 to score
score += 10
```

---

## 🔄 Pull Request Process

### Before Submitting

1. ✅ **Test thoroughly** - Ensure nothing breaks
2. ✅ **Update documentation** - Reflect your changes
3. ✅ **Follow style guide** - PEP 8 compliant
4. ✅ **Commit properly** - Clear, descriptive messages
5. ✅ **Update README** - If adding features

### Commit Message Format
```
type: Brief description (50 chars or less)

Longer explanation if needed (wrap at 72 characters).
Explain WHAT and WHY, not HOW.

Fixes #123
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code formatting (no logic changes)
- `refactor:` Code restructuring
- `perf:` Performance improvements
- `test:` Adding tests
- `chore:` Maintenance tasks

### Examples
```
feat: Add multi-language support for Spanish articles

Implemented trafilatura language detection and filtering for Spanish
content. Updated UI to show detected language.

Fixes #45
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Tested locally
- [ ] Works on Windows
- [ ] Works on Linux/Mac
- [ ] All features still work

## Screenshots (if applicable)
[Add screenshots here]

## Related Issues
Fixes #123
```

---

## 🧪 Testing Guidelines

### Manual Testing Checklist

Before submitting a PR, test:

**Basic Functionality:**
- [ ] Web server starts without errors
- [ ] All three tabs load correctly
- [ ] Scraping works (test with 3-5 articles)
- [ ] Text conversion completes
- [ ] AI summarization completes

**Error Handling:**
- [ ] Invalid URLs handled gracefully
- [ ] Network errors don't crash server
- [ ] Empty results handled properly

**UI/UX:**
- [ ] Progress bars update correctly
- [ ] Logs display properly
- [ ] Buttons enable/disable appropriately
- [ ] No console errors in browser

---

## 🏗️ Project Areas

### Easy (Good First Issues)
- Documentation improvements
- UI/UX enhancements
- Adding example URLs
- Fixing typos
- Updating dependencies

### Medium
- Adding new scraping websites
- Improving error messages
- Performance optimizations
- Adding configuration options

### Advanced
- New AI models integration
- Database support
- API development
- Multi-threading improvements
- Cloud deployment features

---

## 📚 Resources

### Learn About the Stack
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Scrapy Documentation](https://docs.scrapy.org/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

### Understanding the Code
- Read `SETUP_GUIDE.md` for architecture overview
- Check `FEATURES.md` for capability details
- Review existing code and comments
- Ask questions in issues

---

## ❓ Questions?

- **General Questions**: Open a GitHub Discussion
- **Bug Reports**: Create an Issue with the "bug" label
- **Feature Requests**: Create an Issue with the "enhancement" label
- **Security Issues**: Email directly (don't post publicly)

---

## 🎉 Recognition

All contributors will be:
- Listed in the Contributors section
- Mentioned in release notes
- Credited in the README

Thank you for making BOCK Scraper better! 🚀

