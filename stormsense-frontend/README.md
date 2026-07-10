# StormSense AI — Frontend (v1)

**Real-Time Natural Disaster Intelligence Platform**  
AMD Developer Hackathon ACT II 2026 | Track 3 — Unicorn

Built with love for the team. This is a high-quality, production-looking frontend ready for the hackathon.

## What’s Included (Insane Level)

- Dark professional "intel" theme matching the project PDF
- Interactive visual map with clickable disaster markers
- Real-time simulated alerts (new ones appear automatically)
- Risk Score Dashboard with color-coded badges
- Fully working chat connected to the real **7-agent backend pipeline**
- Smooth animations + glassmorphism
- Click markers → see AI Analysis Panel
- Ready for real backend connection

## Setup (Do This Now)

```bash
# Install dependencies
npm install framer-motion lucide-react leaflet react-leaflet @types/leaflet

npm run dev
```

Open http://localhost:3000 — you should see a beautiful dashboard.

## How to Push to Git (Super Important)

**Step-by-step (copy-paste these commands):**

```bash
# 1. Check status
git status

# 2. Stage everything
git add .

# 3. Commit with good message
git commit -m "feat: OP frontend dashboard - live map, real-time alerts, AI chat, risk UI"

# 4. Push
git push origin main
```

**If you never pushed before / first time:**

```bash
git init
git remote add origin <ASK_TEAMMATE_FOR_REPO_URL>
git branch -M main
git add .
git commit -m "Initial commit: StormSense AI frontend v1"
git push -u origin main
```

After pushing, tell your teammate:  
**"Pushed the frontend. Map + alerts + full chat working. Ready for you to connect the backend."**

---

This should look **very strong** for judges. You can keep improving the map / add real Leaflet while he works on connectivity.

Let’s win this. 🔥


This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
