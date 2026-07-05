# Faculty Research Intelligence Platform (FRIP) - PPT Guide

This guide is structured to help you build a comprehensive PowerPoint presentation for the **Faculty Research Intelligence Platform (FRIP)** project. You can copy the content slide-by-slide.

### 🔗 Project & Presentation Resources:
* **Google Slides Presentation Template:** [PPT Slides](https://1drv.ms/p/c/782272E8AC7FB3F7/IQB_v9nl5WlFRLWOLC08Nhb7ATRrm3SIMvnnpQ31vm663DA?e=KgFa7i)
* **Google Drive Reference File:** [Google Drive Reference File](https://drive.google.com/file/d/1qlvypcqBnBna-m7Dl2V2MDCsSE5k7rb_/view?usp=drivesdk)

---

## Slide 1: Title Slide
**Title:** Faculty Research Intelligence Platform (FRIP)
**Subtitle:** AI-Driven Academic Search, Matchmaking, and Analytics
**Speaker/Team:** [Your Name / Team Name]
**Event/Date:** Vardhaman University Hackathon

---

## Slide 2: Problem Statement
**Title:** The Challenge in Academic Research
* **Siloed Knowledge:** Research efforts across departments often happen in isolation, leading to duplicated work and missed collaborative opportunities.
* **Information Overload:** Students and faculty struggle to quickly find highly specific, relevant papers within the university's growing database.
* **Strategic Blind Spots:** Universities lack a systemic way to compare internal research competencies against emerging global trends to identify actionable gaps.
* **Communication Gaps:** Broadcasting targeted academic opportunities or announcements to specific subsets of students and faculty is inefficient.

---

## Slide 3: What is FRIP?
**Title:** Introducing FRIP
* **Overview:** A production-grade enterprise academic portal powered by AI and Natural Language Processing.
* **Core Goal:** To bridge the gap between researchers, students, and global trends.
* **Primary Capabilities:**
  * Context-aware RAG Search
  * Synergy Peer-Matchmaking
  * Global Trend Gap Analysis
  * Targeted Announcement Broadcasting

---

## Slide 4: Feature 1 - Cognitive RAG Chat Search
**Title:** Cognitive RAG Chat Search
* **Multi-Intent Classification:** Automatically understands what the user is looking for (e.g., finding a paper, seeking a mentor, asking a technical question).
* **Contextual Retrieval:** Pulls precise contextual chunks from a vector database (ChromaDB) to answer questions based *strictly* on university publications.
* **External Fallbacks:** Seamlessly falls back to external APIs (arXiv, Tavily Web Search) when local university data lacks the specific information.
* **Interactive Study Rooms:** Dedicated chat threads for specific research papers where students and faculty can discuss findings in real-time.

---

## Slide 5: Feature 2 - Synergy Peer-Matchmaking
**Title:** Intelligent Collaboration Matchmaking
* **Cross-Disciplinary Synergy:** Analyzes research profiles and proposes joint project ideas between professors with complementary interests.
* **Workload Monitoring:** Keeps track of active projects and prevents resource overallocation by monitoring real-time faculty availability.
* **Automated Outreach:** Generates academic email drafts to kickstart collaborative discussions effortlessly.

---

## Slide 6: Feature 3 - Global Trend Gap Analysis
**Title:** Professor Mode: Global Trend & Gap Analysis
* **Benchmarking:** Cross-references internal university competency against web-scale global research milestones.
* **Identifying Blind Spots:** Exposes unexplored domains (e.g., new breakthroughs in Generative AI or IoT).
* **Actionable Proposals:** Suggests new, high-impact research directions and projects to keep the university at the cutting edge of innovation.

---

## Slide 7: Feature 4 - Targeted Broadcasting
**Title:** Targeted Announcements & Communications
* **Precision Targeting:** Send announcements segmented by specific Audience, Department, Year, and Section.
* **Rich Attachments:** Support for file attachments and premium, glassmorphic UI interactions.
* **Real-time Sync:** Uses Supabase for live synchronization of messages and alerts, ensuring critical information reaches the right people immediately.

---

## Slide 8: Live Statistics & Data Integration
**Title:** Data-Driven Dashboard
* **Dynamic Analytics:** The platform live-queries our vector database to present up-to-date metrics.
* **Current Scale (Example metrics):**
  * **14** Unique Research Papers Ingested
  * **673** Vector Chunks Processed
  * **8** Faculty Profiles Analyzed
  * **11** Active Research Domains Tracked
* **Bypassing Quotas:** Implemented sophisticated backend pagination to seamlessly fetch data and bypass cloud provider quota limits, ensuring 100% accuracy in our live stats.

---

## Slide 9: System Architecture & Tech Stack
**Title:** Enterprise System Architecture
* **Frontend:** Glassmorphic UI Dashboard (HTML5, Vanilla CSS, JS)
* **Backend:** FastAPI (Python), providing a high-performance REST API and Serverless (Vercel) readiness.
* **Intelligence Layer (AI):** Groq Llama-3.3 LLM for ultra-fast reasoning, multi-intent classification, and text generation.
* **Vector Storage:** ChromaDB (Cloud) for storing and querying text embedding chunks.
* **Relational Data:** Supabase (PostgreSQL) / SQLite for transaction audit logs, chat history, and announcements CRUD.

---

## Slide 10: Conclusion & Future Scope
**Title:** Conclusion & The Road Ahead
* **Impact:** FRIP transforms an institution's static paper repository into an active, intelligent, and collaborative ecosystem.
* **Future Features:** 
  * Integration with University grading / LMS systems.
  * Expanding the ingestion pipeline to support more formats (Word, LaTeX).
  * Automated grant proposal generation based on gap analysis.
* **Questions?**

---
*Tip for Presenter: Keep the demo ready during Slide 8 to show the real-time dashboard and dynamic stats in action!*
