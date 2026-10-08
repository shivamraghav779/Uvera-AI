import type { AdapterComponents, FrameworkAdapter } from "../types";

import { Alert, Badge, Chart, List, Metric, Progress, Table, Text, Timeline } from "./display";
import { Button, Checkbox, Form, Input, Select } from "./inputs";
import { Card, Divider, Modal, Page, Section, Tabs } from "./layout";

/** The default adapter: implements every semantic component. */
export const shadcnComponents: AdapterComponents = {
  Page,
  Section,
  Card,
  Tabs,
  Modal,
  Divider,
  Metric,
  Text,
  Table,
  Chart,
  List,
  Timeline,
  Badge,
  Progress,
  Alert,
  Form,
  Input,
  Select,
  Checkbox,
  Button,
};

export const shadcnAdapter: FrameworkAdapter = {
  id: "shadcn",
  name: "shadcn/ui",
  components: shadcnComponents,
};
